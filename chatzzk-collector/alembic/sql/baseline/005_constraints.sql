-- 005_constraints.sql

-- [목적] 데이터 무결성 보장 및 Supabase Auth 연동
-- Supabase의 auth.users 테이블(회원가입 시 생성)과 public.users(서비스 유저)를 연결합니다.
-- ON DELETE CASCADE: Supabase 대시보드에서 유저를 삭제하면, 서비스 데이터도 함께 정리되도록 설정합니다.

-- 1. 기존 제약조건이 있다면 충돌 방지를 위해 제거
ALTER TABLE public.users
DROP CONSTRAINT IF EXISTS users_supabase_uid_fkey;

-- 2. 외래 키(Foreign Key) 제약조건 재생성
ALTER TABLE public.users
ADD CONSTRAINT users_supabase_uid_fkey
FOREIGN KEY (supabase_uid)
REFERENCES auth.users(id)
ON DELETE CASCADE;


-- [목적] 유저네임 포맷 및 길이 제한 강제 (데이터 무결성)
-- 애플리케이션 레벨의 검증이 뚫리더라도 DB 차원에서 잘못된 데이터 저장을 방지합니다.
-- 규칙 1: 길이 4~20자
-- 규칙 2: 영문 소문자와 숫자만 허용 (특수문자, 공백, 대문자 불가)

-- 1. 기존 제약조건이 있다면 삭제 (수정사항 반영을 위해)
ALTER TABLE "public"."users"
DROP CONSTRAINT IF EXISTS "check_user_name_format";

-- 2. 체크 제약조건(Check Constraint) 추가
ALTER TABLE "public"."users"
ADD CONSTRAINT "check_user_name_format"
CHECK (
  -- 길이 체크
  char_length(user_name) >= 4 AND char_length(user_name) <= 20
  AND
  -- 형식 체크 (Regex: 시작(^)부터 끝($)까지 소문자(a-z) 또는 숫자(0-9)만 허용)
  user_name ~ '^[a-z0-9]+$'
);
