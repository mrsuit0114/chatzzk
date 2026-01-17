--- 020_triggers.sql

-- [목적] 트리거 이벤트 리스너 등록
-- auth.users 테이블에 INSERT 이벤트가 발생(회원가입)하면 handle_new_user 함수를 실행합니다.

-- 1. 기존 트리거가 있다면 삭제 (중복 실행 방지 및 수정 반영)
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

-- 2. 트리거 생성
-- AFTER INSERT: 유저가 auth.users에 정상적으로 생성된 "직후"에 실행
-- FOR EACH ROW: 각 유저 생성 건마다 개별 실행
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();
