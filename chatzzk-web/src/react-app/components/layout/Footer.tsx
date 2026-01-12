import { Link } from "react-router-dom";
import { Mail } from "lucide-react";

function GithubIcon(props: React.SVGProps<SVGSVGElement>) {
    return (
        <svg
            {...props}
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
            <path d="M9 18c-4.51 2-5-2-7-2" />
        </svg>
    );
}

export function Footer() {
    return (
        <footer className="w-full border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="container mx-auto py-10 md:py-12">
                <div className="grid grid-cols-1 gap-8 md:grid-cols-4">

                    {/* 1. 서비스 소개 */}
                    <div className="md:col-span-2 space-y-4">
                        <h3 className="text-lg font-bold">Stream Analytics</h3>
                        <p className="text-sm text-muted-foreground leading-relaxed max-w-xs">
                            AI 기반 인터넷 방송 분석 서비스.<br />
                            채팅 데이터와 화력을 분석하여 스트리머와 시청자에게 새로운 인사이트를 제공합니다.
                        </p>
                    </div>

                    {/* 2. 빠른 이동 (Sitemap) */}
                    <div className="space-y-4">
                        <h3 className="text-sm font-semibold tracking-wider uppercase">Platform</h3>
                        <ul className="space-y-2 text-sm text-muted-foreground">
                            <li>
                                <Link to="/chzzk" className="hover:text-foreground transition-colors">치지직</Link>
                            </li>
                            <li>
                                <Link to="/youtube" className="hover:text-foreground transition-colors">유튜브</Link>
                            </li>
                            <li>
                                <Link to="/soop" className="hover:text-foreground transition-colors">SOOP</Link>
                            </li>
                        </ul>
                    </div>

                    {/* 3. 연락처 및 소셜 */}
                    <div className="space-y-4">
                        <h3 className="text-sm font-semibold tracking-wider uppercase">Contact</h3>
                        <div className="flex space-x-4">
                            <a
                                href="https://github.com/your-repo"
                                target="_blank"
                                rel="noreferrer"
                                className="text-muted-foreground hover:text-foreground transition-colors"
                                aria-label="Github"
                            >
                                <GithubIcon className="h-5 w-5" />
                            </a>
                            <a
                                href="mailto:contact@example.com"
                                className="text-muted-foreground hover:text-foreground transition-colors"
                                aria-label="Email"
                            >
                                <Mail className="h-5 w-5" />
                            </a>
                        </div>
                        <p className="text-xs text-muted-foreground">
                            문의: contact@stream-analytics.com
                        </p>
                    </div>
                </div>

                {/* 4. 하단 저작권 및 법적 고지 */}
                <div className="mt-10 border-t pt-6 flex flex-col md:flex-row justify-between items-center gap-4">
                    <p className="text-xs text-muted-foreground">
                        © 2024 Stream Analytics. All rights reserved.
                    </p>
                    <div className="flex gap-6 text-xs text-muted-foreground">
                        <Link to="#" className="hover:text-foreground">이용약관</Link>
                        <Link to="#" className="hover:text-foreground">개인정보처리방침</Link>
                    </div>
                </div>
            </div>
        </footer>
    );
}
