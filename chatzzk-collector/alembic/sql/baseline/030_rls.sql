-- 030_rls.sql

-- [목적] 테이블별 Row Level Security (RLS) 활성화
-- RLS를 활성화하면 기본적으로 모든 접근이 차단(Deny All)되며,
-- 이후 040_policies.sql에서 정의할 정책에 의해서만 접근이 허용됩니다.

-- 1. Platforms (공개 테이블이지만 명시적 제어를 위해 활성화)
ALTER TABLE public.platforms ENABLE ROW LEVEL SECURITY;

-- 2. Users (개인 정보)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- 3. Channels (채널 정보)
ALTER TABLE public.channels ENABLE ROW LEVEL SECURITY;

-- 4. Channel Metadata (민감 정보 포함)
ALTER TABLE public.channel_metadata ENABLE ROW LEVEL SECURITY;

-- 5. VODs (핵심 콘텐츠)
ALTER TABLE public.vods ENABLE ROW LEVEL SECURITY;

-- 6. VOD Pipeline Logs (백엔드 전용 로그)
-- 정책을 정의하지 않더라도 활성화하여 외부 접근을 원천 차단합니다.
ALTER TABLE public.vod_pipeline_logs ENABLE ROW LEVEL SECURITY;
