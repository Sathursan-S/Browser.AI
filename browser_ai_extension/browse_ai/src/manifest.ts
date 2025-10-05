import { defineManifest } from '@crxjs/vite-plugin'
import packageData from '../package.json'

//@ts-ignore
const isDev = process.env.NODE_ENV == 'development'

export default defineManifest({
  name: `${packageData.displayName || packageData.name}${isDev ? ` ➡️ Dev` : ''}`,
  description: packageData.description,
  version: packageData.version,
  manifest_version: 3,
  icons: {
    // @ts-ignore
    16: 'img/logo-16.png',
    // @ts-ignore
    32: 'img/logo-32.png',
    // @ts-ignore
    48: 'img/logo-48.png',
    // @ts-ignore
    128: 'img/logo-128.png',
  },
  action: {
    // @ts-ignore
    default_title: 'Click to open Browser.AI Side Panel',
    // @ts-ignore
    default_icon: 'img/logo-48.png',
  },
  // @ts-ignore
  options_page: 'options.html',
  // @ts-ignore
  devtools_page: 'devtools.html',
  background: {
    // @ts-ignore
    service_worker: 'src/background/index.ts',
    type: 'module',
  },
  content_scripts: [
    {
      matches: ['http://*/*', 'https://*/*'],
      // @ts-ignore
      js: ['src/contentScript/index.ts'],
    },
  ],
  side_panel: {
    default_path: 'sidepanel.html',
  },
  web_accessible_resources: [
    {
      resources: ['img/logo-16.png', 'img/logo-32.png', 'img/logo-48.png', 'img/logo-128.png'],
      matches: [],
    },
  ],
  permissions: ['sidePanel', 'storage', 'debugger', 'tabs', 'activeTab'],
  // @ts-ignore
  host_permissions: ['<all_urls>'],
})

