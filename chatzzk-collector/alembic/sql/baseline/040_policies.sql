-- [목적] RLS 정책(Policy) 정의
-- 최적화: `auth.uid()` 호출 비용 절감을 위해 `(select auth.uid())` 래핑 사용
-- 최적화: VOD 조회 정책 통합 (Unified Read Access)

-- =================================================================
-- 0. 기존 정책 초기화 (재실행 가능성 확보)
-- =================================================================
-- Platforms
DROP POLICY IF EXISTS "Public Read Access" ON public.platforms;
-- Users
DROP POLICY IF EXISTS "Read own profile only" ON public.users;
DROP POLICY IF EXISTS "Update own profile only" ON public.users;
-- Channels
DROP POLICY IF EXISTS "Public Read Access" ON public.channels;
DROP POLICY IF EXISTS "Owner Update Access" ON public.channels;
-- Channel Metadata
DROP POLICY IF EXISTS "Owner/Editor Read Access" ON public.channel_metadata;
DROP POLICY IF EXISTS "Owner Update Access" ON public.channel_metadata;
DROP POLICY IF EXISTS "Owner Insert Access" ON public.channel_metadata;
-- VODs (기존 분리된 정책들 모두 삭제)
DROP POLICY IF EXISTS "Conditional Public Access for VODs" ON public.vods;
DROP POLICY IF EXISTS "Owner/Editor Read Access" ON public.vods;
DROP POLICY IF EXISTS "Owner Update Access" ON public.vods;
DROP POLICY IF EXISTS "Unified Read Access" ON public.vods;


-- =================================================================
-- 1. Platforms 테이블 (전체 공개)
-- =================================================================
CREATE POLICY "Public Read Access"
ON public.platforms FOR SELECT USING (true);


-- =================================================================
-- 2. Users 테이블 (본인만 접근)
-- =================================================================
-- [조회] 내 프로필만 조회
CREATE POLICY "Read own profile only"
ON public.users FOR SELECT
USING ( supabase_uid = (select auth.uid()) );

-- [수정] 내 프로필만 수정
CREATE POLICY "Update own profile only"
ON public.users FOR UPDATE
USING ( supabase_uid = (select auth.uid()) );


-- =================================================================
-- 3. Channels 테이블 (조회 공개 / 수정 소유자)
-- =================================================================
-- [조회] 누구나 조회 가능
CREATE POLICY "Public Read Access"
ON public.channels FOR SELECT USING (true);

-- [수정] 소유자만 수정 가능
CREATE POLICY "Owner Update Access"
ON public.channels FOR UPDATE
USING (
  user_id = (SELECT id FROM users WHERE supabase_uid = (select auth.uid()))
);

CREATE POLICY "Owner Insert Access"
ON public.channel_metadata FOR INSERT
WITH CHECK (
  EXISTS (
    SELECT 1 FROM channels c
    WHERE c.id = channel_metadata.channel_id
    AND c.user_id = (SELECT id FROM users WHERE supabase_uid = (select auth.uid()))
  )
);

-- =================================================================
-- 4. Channel Metadata 테이블 (소유자/편집자 전용)
-- =================================================================
-- [조회] 소유자와 편집자만 접근 가능
CREATE POLICY "Owner/Editor Read Access"
ON public.channel_metadata FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM channels c
    WHERE c.id = channel_metadata.channel_id
    AND (
      c.user_id = (SELECT id FROM users WHERE supabase_uid = (select auth.uid()))
      OR
      c.editor_id = (SELECT id FROM users WHERE supabase_uid = (select auth.uid()))
    )
  )
);

-- [수정] 소유자만 수정 가능
CREATE POLICY "Owner Update Access"
ON public.channel_metadata FOR UPDATE
USING (
  EXISTS (
    SELECT 1 FROM channels c
    WHERE c.id = channel_metadata.channel_id
    AND c.user_id = (SELECT id FROM users WHERE supabase_uid = (select auth.uid()))
  )
);


-- =================================================================
-- 5. VODs 테이블 (통합 정책 적용)
-- =================================================================

-- [조회] 통합 정책 (공개 영상 OR 소유자/편집자 권한)
-- 성능을 위해 단일 정책 내에서 OR 조건 처리
CREATE POLICY "Unified Read Access"
ON public.vods FOR SELECT
USING (
  -- [조건 A] 일반 공개: 노출 설정 ON + 수집 허용 + 지연 시간 경과
  (
    is_exposed = true
    AND pipeline_status = 'COMPLETED'::vodpipelinestatus
    AND EXISTS (
      SELECT 1 FROM channels c
      WHERE c.id = vods.channel_id
      AND c.is_collection_enabled = true
      AND (vods.publish_date + (c.vod_exposure_delay_hours * interval '1 hour') <= now())
    )
  )
  OR
  -- [조건 B] 관리자 접근: 소유자 또는 편집자
  (
    EXISTS (
      SELECT 1 FROM channels c
      WHERE c.id = vods.channel_id
      AND (
        c.user_id = (SELECT id FROM users WHERE supabase_uid = (select auth.uid()))
        OR
        c.editor_id = (SELECT id FROM users WHERE supabase_uid = (select auth.uid()))
      )
    )
  )
);

-- [수정] 소유자만 수정 가능 (공개 여부 토글 등)
CREATE POLICY "Owner Update Access"
ON public.vods FOR UPDATE
USING (
  EXISTS (
    SELECT 1 FROM channels c
    WHERE c.id = vods.channel_id
    AND c.user_id = (SELECT id FROM users WHERE supabase_uid = (select auth.uid()))
  )
);
