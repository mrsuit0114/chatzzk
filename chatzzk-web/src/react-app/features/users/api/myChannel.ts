import { api } from "@/lib/api";
import { MyChannelData } from "@shared/types/channel";

type MyChannelResponse = {
    data: MyChannelData;
};

export const getMyChannel = async (): Promise<MyChannelResponse> => {
    // axios interceptor가 자동으로 Authorization 헤더를 붙여준다고 가정합니다.
    // (로그인 상태이므로 토큰이 있을 것임)
    const response = await api.get<MyChannelResponse>('/my/channel');
    return response.data;
};

export type UpdateMetadataParams = {
    streamerNicknames: string[];
    fanNicknames: string[];
    streamerSex: string; // '남성' | '여성'
    additionalInfo: string[];
};

export const updateChannelMetadata = async (params: UpdateMetadataParams) => {
    // PUT /api/my/channel/metadata
    await api.put('/my/channel/metadata', params);
};

export type ChannelSettingsParams = {
    isCollectionEnabled?: boolean;
    vodDetailExposureDelayHours?: number;
    vodExposureDelayHours?: number;
};

export const updateChannelSettings = async (params: ChannelSettingsParams) => {
    await api.patch('/my/channel', params);
};

// --- 2. 편집자 계정 관리 ---

// 조회 응답 타입
export type EditorAccount = {
    id: string;      // 실제 아이디 (도메인 제외)
    isActive: boolean;
} | null;

// 조회
export const getEditorAccount = async (): Promise<EditorAccount> => {
    const { data } = await api.get<{ data: EditorAccount }>('/my/editor');
    return data.data;
};

// 생성
export const createEditorAccount = async (id: string, pw: string) => {
    await api.post('/my/editor', { id, password: pw });
};

// 수정
export const updateEditorAccount = async (params: { id?: string; password?: string }) => {
    await api.put('/my/editor', params);
};

// 상태 토글 (활성/비활성)
export const toggleEditorStatus = async (isActive: boolean) => {
    await api.patch('/my/editor/status', { isActive });
};
