/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_DEV_ADDR: string
  readonly VITE_PROD_ADDR: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}