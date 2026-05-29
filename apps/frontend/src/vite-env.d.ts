/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_DEFAULT_PERIOD: string;
  readonly VITE_DEFAULT_LEVEL: 'undergraduate' | 'postgraduate';
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
