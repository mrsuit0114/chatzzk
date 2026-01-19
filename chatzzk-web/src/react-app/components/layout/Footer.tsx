import { CONTACT_EMAIL } from "@shared/constants/service_codes";

export function Footer() {
    return (
        <footer className="w-full border-t bg-background text-muted-foreground">
            <div className="container mx-auto py-8 px-4 md:px-6">

                {/* 1. 상단: 서비스 로고/설명 + 약관 링크 */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
                    {/* 좌측: 로고 및 한 줄 소개 */}
                    <div>
                        <span className="text-lg font-bold text-foreground block mb-1">CHATZZK</span>
                        <p className="text-sm">
                            인터넷 스트리밍 방송 AI 요약 및 분석 서비스
                        </p>
                    </div>

                    {/* 우측: 약관 및 개인정보처리방침 */}
                    <div className="flex gap-6 text-sm font-medium">
                        <a
                            href="https://www.notion.so/2ecad172fa2180c7a601f6be207f42b4?source=copy_link"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="hover:text-foreground transition-colors"
                        >
                            서비스 이용약관
                        </a>
                        <a
                            href="https://www.notion.so/2ecad172fa21802786ffd0caa11d1f70?source=copy_link"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="hover:text-foreground transition-colors"
                        >
                            개인정보 처리방침
                        </a>
                    </div>
                </div>

                {/* 2. 중단: 핵심 고지사항 (Disclaimer) - 텍스트 위주로 심플하게 */}
                <div className="border-t border-border/50 py-6">
                    <h4 className="sr-only">서비스 고지사항</h4> {/* 스크린리더용 제목 */}
                    <ul className="text-xs leading-relaxed space-y-1 text-muted-foreground/80">
                        <li>
                            <span className="font-semibold mr-1">• 비공식 서비스:</span>
                            본 서비스는 치지직(CHZZK) 플랫폼과 무관한 비공식 서비스입니다.
                        </li>
                        <li>
                            <span className="font-semibold mr-1">• 저작권 귀속:</span>
                            본 서비스는 스트리머의 사전 허가를 받은 채널의 공개 방송 데이터만을 수집·분석합니다.
                            방송 콘텐츠의 저작권은 각 스트리머에게 있으며, 본 서비스는 원본 콘텐츠를 제공하지 않고
                            분석·요약된 결과 정보만을 제공합니다.
                        </li>
                        <li>
                            <span className="font-semibold mr-1">• AI 분석의 한계:</span>
                            제공되는 요약 및 감정 분석 데이터는 AI 모델에 의해 자동 생성된 것으로, 사실과 다르거나 부정확할 수 있습니다.
                        </li>
                        <li>
                            <span className="font-semibold mr-1">• 광고 운영:</span>
                            향후 원활한 서버 운영 및 서비스 유지를 위해 웹사이트 내 일부 영역에 광고가 포함될 수 있습니다.
                        </li>
                    </ul>
                </div>

                {/* 3. 하단: Copyright + 이메일 */}
                <div className="flex flex-col md:flex-row justify-between items-center gap-2 pt-2 text-xs text-muted-foreground/60">
                    <p>
                        © 2026 CHATZZK Analytics. All rights reserved.
                    </p>
                    <p>
                        문의: {CONTACT_EMAIL}
                    </p>
                </div>
            </div>
        </footer>
    );
}
