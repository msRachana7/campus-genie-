/// <reference types="vite/client" />

interface ImportMetaEnv {
    readonly VITE_API_BASE_URL?: string
    readonly VITE_FRONTEND_FORGE_API_KEY?: string
    readonly VITE_FRONTEND_FORGE_API_URL?: string
    readonly VITE_OAUTH_PORTAL_URL?: string
    readonly VITE_APP_ID?: string
}

interface ImportMeta {
    readonly env: ImportMetaEnv
}