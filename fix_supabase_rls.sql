-- =============================================
-- Supabase RLS Fix for IT Newsroom
-- 실행 위치: Supabase Dashboard > SQL Editor
-- =============================================
-- 현재 문제: anon/publishable 키로는 INSERT/UPDATE 불가 (RLS 차단)
-- 해결: global_stats, daily_stats, feeds, archives, comments 테이블에
--       anon 역할의 쓰기 정책 추가

-- 1. global_stats — 조회 + 업데이트 허용
DROP POLICY IF EXISTS "Allow anon read global_stats" ON global_stats;
DROP POLICY IF EXISTS "Allow anon update global_stats" ON global_stats;
DROP POLICY IF EXISTS "Allow anon insert global_stats" ON global_stats;

CREATE POLICY "Allow anon read global_stats"
    ON global_stats FOR SELECT TO anon USING (true);

CREATE POLICY "Allow anon update global_stats"
    ON global_stats FOR UPDATE TO anon USING (true) WITH CHECK (true);

CREATE POLICY "Allow anon insert global_stats"
    ON global_stats FOR INSERT TO anon WITH CHECK (true);


-- 2. daily_stats — 조회 + 삽입 + 업데이트 허용
DROP POLICY IF EXISTS "Allow anon read daily_stats" ON daily_stats;
DROP POLICY IF EXISTS "Allow anon insert daily_stats" ON daily_stats;
DROP POLICY IF EXISTS "Allow anon update daily_stats" ON daily_stats;

CREATE POLICY "Allow anon read daily_stats"
    ON daily_stats FOR SELECT TO anon USING (true);

CREATE POLICY "Allow anon insert daily_stats"
    ON daily_stats FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "Allow anon update daily_stats"
    ON daily_stats FOR UPDATE TO anon USING (true) WITH CHECK (true);


-- 3. feeds — 조회 + 삽입 + 삭제 허용 (Admin 패널용)
DROP POLICY IF EXISTS "Allow anon read feeds" ON feeds;
DROP POLICY IF EXISTS "Allow anon insert feeds" ON feeds;
DROP POLICY IF EXISTS "Allow anon delete feeds" ON feeds;

CREATE POLICY "Allow anon read feeds"
    ON feeds FOR SELECT TO anon USING (true);

CREATE POLICY "Allow anon insert feeds"
    ON feeds FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "Allow anon delete feeds"
    ON feeds FOR DELETE TO anon USING (true);


-- 4. archives — 조회 + 삽입 + 업서트 허용 (분석 결과 저장용)
DROP POLICY IF EXISTS "Allow anon read archives" ON archives;
DROP POLICY IF EXISTS "Allow anon insert archives" ON archives;
DROP POLICY IF EXISTS "Allow anon update archives" ON archives;

CREATE POLICY "Allow anon read archives"
    ON archives FOR SELECT TO anon USING (true);

CREATE POLICY "Allow anon insert archives"
    ON archives FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "Allow anon update archives"
    ON archives FOR UPDATE TO anon USING (true) WITH CHECK (true);


-- 5. comments — 조회 + 삽입 + 삭제 허용
DROP POLICY IF EXISTS "Allow anon read comments" ON comments;
DROP POLICY IF EXISTS "Allow anon insert comments" ON comments;
DROP POLICY IF EXISTS "Allow anon delete comments" ON comments;

CREATE POLICY "Allow anon read comments"
    ON comments FOR SELECT TO anon USING (true);

CREATE POLICY "Allow anon insert comments"
    ON comments FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "Allow anon delete comments"
    ON comments FOR DELETE TO anon USING (true);


-- 확인: RLS 활성화 상태 확인
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('global_stats', 'daily_stats', 'feeds', 'archives', 'comments');
