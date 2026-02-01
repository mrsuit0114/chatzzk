import { useEffect } from "react";
import { useLocation } from "react-router-dom";

export function ScrollToTop() {
    const { pathname } = useLocation();

    useEffect(() => {
        // 경로(pathname)가 바뀔 때마다 실행
        window.scrollTo(0, 0);
    }, [pathname]);

    return null; // 화면에 아무것도 렌더링하지 않음
}
