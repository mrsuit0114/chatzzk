import {
    Pagination,
    PaginationContent,
    PaginationItem,
    PaginationLink,
    PaginationNext,
    PaginationPrevious,
} from "@/components/ui/pagination";

interface Props {
    total: number;      // 전체 페이지 수
    page: number;       // 현재 페이지
    onChange: (page: number) => void;
    blockSize?: number; // 한 번에 보여줄 페이지 번호 개수
}

// 한 번에 보여줄 페이지 번호 개수 (상수 or props로 관리)

export function BasePagination({ total, page, onChange, blockSize = 5 }: Props) {
    // 1. 현재 페이지가 속한 그룹(Block) 계산
    // 예: page 3 -> group 0 (0~4), page 6 -> group 1 (5~9)
    // 계산 편의를 위해 1부터 시작하는 그룹으로 계산:
    const currentGroup = Math.ceil(page / blockSize);

    // 2. 현재 그룹의 시작 번호와 끝 번호 계산
    const startPage = (currentGroup - 1) * blockSize + 1;
    const endPage = Math.min(total, startPage + blockSize - 1);

    // 3. 페이지 번호 배열 생성
    const pages = [];
    for (let i = startPage; i <= endPage; i++) {
        pages.push(i);
    }

    // 이전 그룹이 존재하는지 여부
    const hasPrevBlock = startPage > 1;
    // 다음 그룹이 존재하는지 여부
    const hasNextBlock = endPage < total;

    return (
        <Pagination className="mt-8">
            <PaginationContent>

                {/* [이전 그룹] 버튼: 이전 블록이 있을 때만 표시 */}
                {hasPrevBlock && (
                    <PaginationItem>
                        <PaginationPrevious
                            href="#"
                            onClick={(e) => {
                                e.preventDefault();
                                // 이전 그룹의 '마지막 번호'로 이동 (예: 6페이지에서 누르면 5페이지로)
                                // 혹은 startPage - 1 로 이동
                                onChange(startPage - 1);
                            }}
                            className="cursor-pointer"
                        />
                    </PaginationItem>
                )}

                {/* 페이지 번호들 (현재 그룹 내의 번호만 렌더링) */}
                {pages.map((p) => (
                    <PaginationItem key={p}>
                        <PaginationLink
                            href="#"
                            isActive={page === p}
                            onClick={(e) => {
                                e.preventDefault();
                                onChange(p);
                            }}
                        >
                            {p}
                        </PaginationLink>
                    </PaginationItem>
                ))}

                {/* [다음 그룹] 버튼: 다음 블록이 있을 때만 표시 */}
                {hasNextBlock && (
                    <PaginationItem>
                        <PaginationNext
                            href="#"
                            onClick={(e) => {
                                e.preventDefault();
                                // 다음 그룹의 '시작 번호'로 이동 (예: 5페이지에서 누르면 6페이지로)
                                onChange(endPage + 1);
                            }}
                            className="cursor-pointer"
                        />
                    </PaginationItem>
                )}

            </PaginationContent>
        </Pagination>
    );
}
