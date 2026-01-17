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
  _user_name := new.raw_user_meta_data ->> 'user_name';

  -- 2. [유효성 검증] user_name이 없거나 공백일 경우 회원가입 트랜잭션 자체를 롤백(차단)시킴
  IF _user_name IS NULL OR length(trim(_user_name)) < 1 THEN
    RAISE EXCEPTION 'User name is required.';
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
  streamer_nicknames text[],
  streamer_sex text,
  fan_nicknames text[],
  additional_info text[]
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
    -- JSONB -> Text Array 변환
    ARRAY(SELECT jsonb_array_elements_text(COALESCE(cm.attributes->'streamer_nicknames', '[]'::jsonb)))::text[],
    (cm.attributes->>'streamer_sex')::text,
    ARRAY(SELECT jsonb_array_elements_text(COALESCE(cm.attributes->'fan_nicknames', '[]'::jsonb)))::text[],
    ARRAY(SELECT jsonb_array_elements_text(COALESCE(cm.attributes->'additional_info', '[]'::jsonb)))::text[]
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
  p_streamer_nicknames text[],
  p_fan_nicknames text[],
  p_streamer_sex text,
  p_additional_info text[]
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

  v_new_attributes := jsonb_build_object(
    'streamer_nicknames', to_jsonb(p_streamer_nicknames),
    'fan_nicknames', to_jsonb(p_fan_nicknames),
    'streamer_sex', to_jsonb(p_streamer_sex),
    'additional_info', to_jsonb(p_additional_info)
  );

  -- UPSERT 로직 (존재하면 수정, 없으면 생성)
  INSERT INTO channel_metadata (channel_id, attributes, updated_at)
  VALUES (v_channel_id, v_new_attributes, now())
  ON CONFLICT (channel_id)
  DO UPDATE SET
    attributes = EXCLUDED.attributes,
    updated_at = now();

  RETURN true;
END;
$$ LANGUAGE plpgsql;
