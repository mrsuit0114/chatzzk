-- 1. Schema Usage
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;

-- 2. Service Role (Superuser-like) - 모든 권한 부여 [수정됨]
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT ALL ON ALL ROUTINES IN SCHEMA public TO service_role;

-- 3. Table Access (SELECT) - 일반 유저
GRANT SELECT ON TABLE public.platforms TO anon, authenticated;
GRANT SELECT ON TABLE public.users TO anon, authenticated;
GRANT SELECT ON TABLE public.channels TO anon, authenticated;
GRANT SELECT ON TABLE public.channel_metadata TO anon, authenticated;
GRANT SELECT ON TABLE public.vods TO anon, authenticated;
GRANT SELECT ON TABLE public.vod_pipeline_logs TO anon, authenticated;

-- 4. Table Access (UPDATE/INSERT) - 로그인 유저
GRANT UPDATE ON TABLE public.users TO authenticated;
GRANT UPDATE ON TABLE public.channels TO authenticated;
GRANT UPDATE ON TABLE public.vods TO authenticated;

GRANT UPDATE, INSERT ON TABLE public.channel_metadata TO authenticated;

-- 5. Sequence Usage
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;


-- =================================================================
-- [중요] 함수 실행 권한 (Function Execute)
-- =================================================================

-- 1. 공개 함수
GRANT EXECUTE ON FUNCTION public.search_vods TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.search_channels TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_channel_detail TO anon, authenticated, service_role;

-- 2. 비공개 함수
GRANT EXECUTE ON FUNCTION public.get_my_channel TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_my_vods TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.update_vod_exposure TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.update_channel_metadata TO authenticated, service_role;
