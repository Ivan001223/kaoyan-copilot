const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Alert {
    has_critical_update?: boolean;
    has_relevant_news?: boolean;
    message?: string;
    source_url?: string;
    news_items?: any[];
    last_check?: number;
    [key: string]: any;
}

export interface HistorySession {
    id: string;
    title: string;
    messages: any[];
    updated_at: number;
}

export const api = {
    // 1. Quote
    getQuote: async () => {
        const res = await fetch(`${API_BASE_URL}/quote`);
        return res.json();
    },

    // 2. Alerts
    getAlerts: async () => {
        const res = await fetch(`${API_BASE_URL}/alerts`);
        return res.json();
    },

    checkRadar: async () => {
        const res = await fetch(`${API_BASE_URL}/radar/check`, { method: 'POST' });
        if (!res.ok) throw new Error('Failed to check radar');
        return res.json();
    },

    checkPolitics: async () => {
        const res = await fetch(`${API_BASE_URL}/politics/check`, { method: 'POST' });
        if (!res.ok) throw new Error('Failed to check politics');
        return res.json();
    },

    // 3. History
    getHistory: async (userId: string) => {
        const res = await fetch(`${API_BASE_URL}/history/${userId}`);
        return res.json();
    },

    saveSession: async (userId: string, sessionId: string, messages: any[], title?: string) => {
        const res = await fetch(`${API_BASE_URL}/history/${userId}/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                messages: messages,
                title: title
            })
        });
        if (!res.ok) throw new Error('Failed to save session');
        return res.json();
    },

    deleteSession: async (userId: string, sessionId: string) => {
        const res = await fetch(`${API_BASE_URL}/history/${userId}/${sessionId}`, {
            method: 'DELETE',
        });
        if (!res.ok) throw new Error('Failed to delete session');
        return res.json();
    },

    // 4. Settings
    getSettings: async () => {
        const res = await fetch(`${API_BASE_URL}/settings`);
        return res.json();
    },

    // 5. Uploads
    uploadDocuments: async (files: File[]) => {
        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });
        
        const res = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData,
        });

        if (!res.ok) throw new Error('文档上传失败');
        return res.json();
    },

    uploadImage: async (file: File) => {
        const formData = new FormData();
        formData.append('file', file);

        const res = await fetch(`${API_BASE_URL}/upload/image`, {
            method: 'POST',
            body: formData,
        });

        if (!res.ok) throw new Error('图片上传失败');
        return res.json();
    }
};
