-- 010_functions.sql

-- [목적] 유저 회원가입 트리거 로직 처리
-- Supabase Auth에 유저가 생성될 때, public.users 테이블에도 자동으로 데이터를 동기화합니다.
-- SECURITY DEFINER: 이 함수는 호출한 사용자의 권한이 아닌, 함수 생성자(Admin/Postgres)의 권한으로 실행되어 RLS를 우회합니다.

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
DECLARE
  _user_name text;
BEGIN
  -- 1. 회원가입 시 전달된 메타데이터에서 user_name 추출
  -- (Client 측에서 supabase.auth.signUp({ options: { data: { user_name: ... } } }) 형태로 보낸 값)
  _user_name := split_part(new.email, '@', 1);

  -- 2. [유효성 검증] user_name이 없거나 공백일 경우 회원가입 트랜잭션 자체를 롤백(차단)시킴
  IF _user_name IS NULL OR length(trim(_user_name)) < 1 THEN
    RAISE EXCEPTION 'Cannot extract username from email.';
  END IF;

  -- 3. public.users 테이블에 동기화 데이터 삽입
  INSERT INTO public.users (
    supabase_uid,
    user_name,
    role,
    created_at
  )
  VALUES (
    new.id,                   -- auth.users의 UUID
    _user_name,               -- 추출한 유저명
    'USER'::public.userrole,  -- 기본 권한 설정 (Enum 타입 캐스팅 주의)
    new.created_at            -- 가입 시간 동기화
  );

  RETURN new;
END;
$$;

-- [검색] VOD 검색 (필터, 페이징, RLS 처리 포함)
-- 공개된 영상만 검색하며, 채널의 노출 지연 시간 등을 고려합니다.
DROP FUNCTION IF EXISTS search_vods;
CREATE OR REPLACE FUNCTION search_vods(
  p_platform_code text,
  p_query text,
  p_page int,
  p_page_size int,
  p_from_date timestamptz DEFAULT NULL,
  p_to_date timestamptz DEFAULT NULL,
  p_channel_id text DEFAULT NULL
)
RETURNS TABLE (
  video_no text,
  video_title text,
  publish_date timestamptz,
  duration int,
  channel_name text,
  channel_id text,
  total_count bigint
)
SET search_path = public
AS $$
DECLARE
  v_offset int;
BEGIN
  -- 페이지 방어 로직
  IF p_page < 1 THEN p_page := 1; END IF;
  v_offset := (p_page - 1) * p_page_size;

  RETURN QUERY
  WITH filtered_vods AS (
    SELECT
      v.video_no::text,
      v.video_title::text,
      v.publish_date,
      v.duration,
      c.channel_name::text,
      c.platform_channel_id::text AS channel_id,
      c.vod_exposure_delay_hours
    FROM vods v
    JOIN channels c ON v.channel_id = c.id
    JOIN platforms p ON c.platform_id = p.id
    WHERE
      -- 1. 플랫폼 필터
      (p_platform_code IS NULL OR p.platform_code = p_platform_code::platformcode)
      -- 2. 특정 채널 필터
      AND (p_channel_id IS NULL OR c.platform_channel_id = p_channel_id)
      -- 3. 공개 정책 (수동 RLS)
      AND v.is_exposed = true
      AND v.pipeline_status = 'COMPLETED'::vodpipelinestatus
      AND c.is_collection_enabled = true
      AND (v.publish_date + (c.vod_exposure_delay_hours * interval '1 hour') <= now())
      -- 4. 검색어 (제목 or 채널명)
      AND (
        p_query IS NULL OR p_query = '' OR
        v.video_title ILIKE '%' || p_query || '%' OR
        c.channel_name ILIKE '%' || p_query || '%'
      )
      -- 5. 기간 필터
      AND (p_from_date IS NULL OR v.publish_date >= p_from_date)
      AND (p_to_date IS NULL OR v.publish_date <= p_to_date)
  )
  SELECT
    f.video_no,
    f.video_title,
    f.publish_date,
    f.duration,
    f.channel_name,
    f.channel_id,
    (SELECT COUNT(*) FROM filtered_vods)::bigint as total_count
  FROM filtered_vods f
  ORDER BY f.publish_date DESC
  LIMIT p_page_size
  OFFSET v_offset;
END;
$$ LANGUAGE plpgsql;


-- [검색] 채널 검색
DROP FUNCTION IF EXISTS search_channels;
CREATE OR REPLACE FUNCTION search_channels(
  p_platform_code text,
  p_query text,
  p_page int,
  p_page_size int
)
RETURNS TABLE (
  platform_code text,
  platform_channel_id text,
  channel_name text,
  total_count bigint
)
SET search_path = public
AS $$
DECLARE
  v_offset int;
BEGIN
  IF p_page < 1 THEN p_page := 1; END IF;
  v_offset := (p_page - 1) * p_page_size;

  RETURN QUERY
  WITH filtered_channels AS (
    SELECT
      p.platform_code::text,
      c.platform_channel_id::text,
      c.channel_name::text
    FROM channels c
    JOIN platforms p ON c.platform_id = p.id
    WHERE
      (p_platform_code IS NULL OR p_platform_code = 'ALL' OR p.platform_code = p_platform_code::platformcode)
      AND (
        p_query IS NULL OR p_query = '' OR
        c.channel_name ILIKE '%' || p_query || '%' OR
        c.platform_channel_id = p_query
      )
  )
  SELECT
    f.platform_code,
    f.platform_channel_id,
    f.channel_name,
    (SELECT COUNT(*) FROM filtered_channels)::bigint as total_count
  FROM filtered_channels f
  ORDER BY f.channel_name ASC
  LIMIT p_page_size
  OFFSET v_offset;
END;
$$ LANGUAGE plpgsql;


-- [조회] 단일 채널 상세 정보 조회 (Public)
DROP FUNCTION IF EXISTS get_channel_detail;
CREATE OR REPLACE FUNCTION get_channel_detail(
  p_platform_code text,
  p_platform_channel_id text
)
RETURNS TABLE (
  channel_id bigint,
  platform_code text,
  platform_channel_id text,
  channel_name text,
  last_vod_crawled_at timestamptz,
  vod_exposure_delay_hours int,
  vod_detail_exposure_delay_hours int,
  is_collection_enabled boolean
)
SET search_path = public
AS $$
BEGIN
  RETURN QUERY
  SELECT
    c.id::bigint,
    p.platform_code::text,
    c.platform_channel_id::text,
    c.channel_name::text,
    c.last_vod_crawled_at,
    c.vod_exposure_delay_hours::int,
    c.vod_detail_exposure_delay_hours::int,
    c.is_collection_enabled::boolean
  FROM channels c
  JOIN platforms p ON c.platform_id = p.id
  WHERE c.platform_channel_id = p_platform_channel_id
    AND p.platform_code = p_platform_code::platformcode;
END;
$$ LANGUAGE plpgsql;


-- [마이페이지] 내 채널 정보 및 메타데이터 조회
-- 소유자(Owner) 혹은 편집자(Editor) 권한이 있는 채널을 반환합니다.
CREATE OR REPLACE FUNCTION get_my_channel()
RETURNS TABLE (
  channel_id bigint,
  platform_code text,
  platform_channel_id text,
  channel_name text,
  last_vod_crawled_at timestamptz,
  vod_exposure_delay_hours int,
  vod_detail_exposure_delay_hours int,
  is_collection_enabled bool,
  metadata jsonb
)
SET search_path = public
AS $$
DECLARE
  v_internal_user_id int;
BEGIN
  SELECT id INTO v_internal_user_id
  FROM users
  WHERE supabase_uid = auth.uid();

  IF v_internal_user_id IS NULL THEN
    RETURN;
  END IF;

  RETURN QUERY
  SELECT
    c.id::bigint,
    p.platform_code::text,
    c.platform_channel_id::text,
    c.channel_name::text,
    c.last_vod_crawled_at,
    c.vod_exposure_delay_hours::int,
    c.vod_detail_exposure_delay_hours::int,
    c.is_collection_enabled,
    COALESCE(cm.attributes, '{}'::jsonb)
  FROM channels c
  JOIN platforms p ON c.platform_id = p.id
  LEFT JOIN channel_metadata cm ON c.id = cm.channel_id
  WHERE
    c.user_id = v_internal_user_id
    OR c.editor_id = v_internal_user_id;
END;
$$ LANGUAGE plpgsql;


-- [관리] VOD 노출 여부 토글 (소유자 전용)
CREATE OR REPLACE FUNCTION update_vod_exposure(
  p_video_no text,
  p_platform_code text,
  p_platform_channel_id text,
  p_is_exposed boolean
)
RETURNS boolean
SET search_path = public
AS $$
DECLARE
  v_internal_user_id int;
  v_updated_rows int;
BEGIN
  SELECT id INTO v_internal_user_id
  FROM users
  WHERE supabase_uid = auth.uid();

  UPDATE vods
  SET
    is_exposed = p_is_exposed,
    updated_at = now()
  FROM channels c
  JOIN platforms p ON c.platform_id = p.id
  WHERE vods.channel_id = c.id
    AND vods.video_no = p_video_no
    AND c.platform_channel_id = p_platform_channel_id
    AND p.platform_code = p_platform_code::platformcode
    AND c.user_id = v_internal_user_id; -- 소유자 검증

  GET DIAGNOSTICS v_updated_rows = ROW_COUNT;
  RETURN v_updated_rows > 0;
END;
$$ LANGUAGE plpgsql;


-- [마이페이지] 내 VOD 관리 목록 조회 (소유자/편집자)
CREATE OR REPLACE FUNCTION get_my_vods(
  p_page int,
  p_page_size int,
  p_query text DEFAULT NULL,
  p_visibility text DEFAULT 'ALL',
  p_from_date timestamptz DEFAULT NULL,
  p_to_date timestamptz DEFAULT NULL
)
RETURNS TABLE (
  video_no text,
  video_title text,
  publish_date timestamptz,
  duration int,
  channel_id text,
  channel_name text,
  platform_code text,
  pipeline_status text,
  is_exposed bool,
  total_count bigint
)
SET search_path = public
AS $$
DECLARE
  v_offset int;
  v_internal_user_id int;
BEGIN
  IF p_page < 1 THEN p_page := 1; END IF;
  v_offset := (p_page - 1) * p_page_size;

  SELECT id INTO v_internal_user_id
  FROM users
  WHERE supabase_uid = auth.uid();

  RETURN QUERY
  WITH my_vods AS (
    SELECT
      v.video_no::text,
      v.video_title::text,
      v.publish_date,
      v.duration,
      c.platform_channel_id::text as channel_id,
      c.channel_name::text,
      p.platform_code::text,
      v.pipeline_status::text,
      v.is_exposed
    FROM vods v
    JOIN channels c ON v.channel_id = c.id
    JOIN platforms p ON c.platform_id = p.id
    WHERE
      (c.user_id = v_internal_user_id OR c.editor_id = v_internal_user_id)
      AND (p_query IS NULL OR p_query = '' OR v.video_title ILIKE '%' || p_query || '%')
      AND (
        p_visibility = 'ALL'
        OR (p_visibility = 'PUBLIC' AND v.is_exposed = true)
        OR (p_visibility = 'PRIVATE' AND v.is_exposed = false)
      )
      AND (p_from_date IS NULL OR v.publish_date >= p_from_date)
      AND (p_to_date IS NULL OR v.publish_date <= p_to_date)
  )
  SELECT
    m.video_no,
    m.video_title,
    m.publish_date,
    m.duration,
    m.channel_id,
    m.channel_name,
    m.platform_code,
    m.pipeline_status,
    m.is_exposed,
    (SELECT COUNT(*) FROM my_vods)::bigint as total_count
  FROM my_vods m
  ORDER BY m.publish_date DESC
  LIMIT p_page_size
  OFFSET v_offset;
END;
$$ LANGUAGE plpgsql;


-- [마이페이지] 채널 메타데이터 업데이트 (Upsert 적용)
CREATE OR REPLACE FUNCTION update_channel_metadata(
  p_attributes jsonb
)
RETURNS boolean
SET search_path = public
AS $$
DECLARE
  v_internal_user_id int;
  v_channel_id int;
  v_new_attributes jsonb;
BEGIN
  SELECT id INTO v_internal_user_id
  FROM users
  WHERE supabase_uid = auth.uid();

  SELECT id INTO v_channel_id
  FROM channels
  WHERE user_id = v_internal_user_id
  LIMIT 1;

  IF v_channel_id IS NULL THEN
    RETURN false;
  END IF;

  INSERT INTO channel_metadata (channel_id, attributes, updated_at)
  VALUES (v_channel_id, p_attributes, now())
  ON CONFLICT (channel_id)
  DO UPDATE SET
    attributes = EXCLUDED.attributes,
    updated_at = now();

  RETURN true;
END;
$$ LANGUAGE plpgsql;


-- [Admin] 채널 추가 및 초기 메타데이터 설정 (옵션: 유저 매핑)
CREATE OR REPLACE FUNCTION add_new_channel_with_metadata(
  p_platform_code text,        -- 'CHZZK', 'SOOP' 등
  p_platform_channel_id text,  -- 채널 고유 ID
  p_channel_name text,         -- 채널명
  p_attributes jsonb,          -- 메타데이터 (SnakeCase JSON)
  p_target_user_name text DEFAULT NULL -- 연결할 유저 ID (없으면 NULL)
)
RETURNS jsonb
SET search_path = public
AS $$
DECLARE
  v_platform_id int;
  v_user_id int;
  v_channel_id int;
  v_current_role userrole;
BEGIN
  -- 1. 플랫폼 ID 조회
  SELECT id INTO v_platform_id
  FROM platforms
  WHERE platform_code = p_platform_code::platformcode;

  IF v_platform_id IS NULL THEN
    RAISE EXCEPTION 'Invalid platform code: %', p_platform_code;
  END IF;

  -- 2. 유저 매핑 로직 (target_user_name이 들어온 경우)
  IF p_target_user_name IS NOT NULL AND p_target_user_name <> '' THEN
    -- 유저 조회
    SELECT id, role INTO v_user_id, v_current_role
    FROM users
    WHERE user_name = p_target_user_name;

    IF v_user_id IS NULL THEN
      RAISE EXCEPTION 'User not found: %', p_target_user_name;
    END IF;

    -- 유저 권한 승격 (이미 ADMIN이나 OWNER가 아니라면 OWNER로 설정)
    IF v_current_role = 'USER'::userrole THEN
      UPDATE users
      SET role = 'OWNER'::userrole
      WHERE id = v_user_id;
    END IF;
  ELSE
    -- 유저 매핑을 안 하는 경우 NULL로 설정
    v_user_id := NULL;
  END IF;

  -- 3. 채널 생성 (이미 존재하면 에러 발생 - Unique Constraint)
  INSERT INTO channels (
    platform_id,
    platform_channel_id,
    channel_name,
    user_id, -- 매핑된 유저 ID (혹은 NULL)
    is_collection_enabled
  )
  VALUES (
    v_platform_id,
    p_platform_channel_id,
    p_channel_name,
    v_user_id,
    true -- 기본적으로 수집 활성화
  )
  RETURNING id INTO v_channel_id;

  -- 4. 메타데이터 생성
  INSERT INTO channel_metadata (
    channel_id,
    attributes
  )
  VALUES (
    v_channel_id,
    p_attributes
  );

  -- 5. 결과 반환
  RETURN jsonb_build_object(
    'success', true,
    'channel_id', v_channel_id,
    'user_id', v_user_id
  );

EXCEPTION WHEN unique_violation THEN
  -- 채널 중복 에러 캐치 (Postgres Error Code 23505)
  RAISE EXCEPTION 'Channel already exists';
END;
$$ LANGUAGE plpgsql;

-- [Admin] 채널 소유권 이전 (Transfer Ownership)
-- 1. 현재 소유자가 있다면 USER로 강등
-- 2. 새 대상 유저가 OWNER가 될 자격이 있는지 검증 (기존 채널 없음, 현재 USER 권한)
-- 3. 새 유저를 OWNER로 승격하고 채널에 매핑
CREATE OR REPLACE FUNCTION transfer_channel_ownership(
  p_channel_id bigint,
  p_new_user_name text
)
RETURNS jsonb
SET search_path = public
AS $$
DECLARE
  v_current_user_id int;
  v_new_user_id int;
  v_new_user_role userrole;
  v_new_user_channel_count int;
BEGIN
  -- 1. 대상 채널 및 현재 소유자 확인
  SELECT user_id INTO v_current_user_id
  FROM channels
  WHERE id = p_channel_id;

  -- 2. 새 소유자 후보 조회
  SELECT id, role INTO v_new_user_id, v_new_user_role
  FROM users
  WHERE user_name = p_new_user_name;

  -- [검증 1] 유저 존재 여부
  IF v_new_user_id IS NULL THEN
    RAISE EXCEPTION 'Target user not found: %', p_new_user_name;
  END IF;

  -- [검증 2] 새 유저가 이미 다른 채널을 소유 중인지 확인 (Uniqueness)
  SELECT count(*) INTO v_new_user_channel_count
  FROM channels
  WHERE user_id = v_new_user_id;

  IF v_new_user_channel_count > 0 THEN
    RAISE EXCEPTION 'Target user already owns a channel. Cannot map multiple channels.';
  END IF;

  -- [검증 3] 새 유저의 권한이 USER인지 확인 (이미 관리자거나 OWNER면 실수일 가능성 높음)
  IF v_new_user_role <> 'USER'::userrole THEN
    RAISE EXCEPTION 'Target user role must be USER. Current role: %', v_new_user_role;
  END IF;

  -- ---------------------------------------------------
  -- 로직 실행 (트랜잭션)
  -- ---------------------------------------------------

  -- 3. 기존 소유자가 있다면 -> USER로 강등 (권한 박탈)
  IF v_current_user_id IS NOT NULL THEN
    UPDATE users
    SET role = 'USER'::userrole
    WHERE id = v_current_user_id;
  END IF;

  -- 4. 새 소유자 -> OWNER로 승격
  UPDATE users
  SET role = 'OWNER'::userrole
  WHERE id = v_new_user_id;

  -- 5. 채널의 주인 변경
  UPDATE channels
  SET user_id = v_new_user_id,
      updated_at = now()
  WHERE id = p_channel_id;

  RETURN jsonb_build_object(
    'success', true,
    'old_owner_id', v_current_user_id,
    'new_owner_id', v_new_user_id
  );
END;
$$ LANGUAGE plpgsql;
