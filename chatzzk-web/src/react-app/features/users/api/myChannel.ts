import { api } from "@/lib/api";
import { ChannelMetadata, MyChannelData } from "@shared/types/channel";

type MyChannelResponse = {
    data: MyChannelData;
};

export const getMyChannel = async (): Promise<MyChannelData> => {
    const response = await api.get<MyChannelResponse>('/my/channel');
    return response.data.data;
};

export const updateChannelMetadata = async (metadata: ChannelMetadata) => {
    // 이제 params를 찢어서 정의할 필요 없이 가공된 타입을 그대로 보냅니다.
    const response = await api.put('/my/channel/metadata', metadata);
    return response.data;
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
