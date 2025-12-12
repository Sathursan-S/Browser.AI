// vite.config.ts
import { defineConfig } from "file:///E:/Projects/Projects/Browser.AI/Browser.AI/browser_ai_extension/browse_ai/node_modules/vite/dist/node/index.js";
import { crx } from "file:///E:/Projects/Projects/Browser.AI/Browser.AI/browser_ai_extension/browse_ai/node_modules/@crxjs/vite-plugin/dist/index.mjs";
import react from "file:///E:/Projects/Projects/Browser.AI/Browser.AI/browser_ai_extension/browse_ai/node_modules/@vitejs/plugin-react/dist/index.js";

// src/manifest.ts
import { defineManifest } from "file:///E:/Projects/Projects/Browser.AI/Browser.AI/browser_ai_extension/browse_ai/node_modules/@crxjs/vite-plugin/dist/index.mjs";

// package.json
var package_default = {
  name: "browse_ai",
  displayName: "browse_ai",
  version: "0.0.0",
  author: "**",
  description: "",
  type: "module",
  license: "MIT",
  keywords: [
    "chrome-extension",
    "react",
    "vite",
    "create-chrome-ext"
  ],
  engines: {
    node: ">=14.18.0"
  },
  scripts: {
    dev: "vite",
    build: "tsc && vite build",
    preview: "vite preview",
    fmt: "prettier --write '**/*.{tsx,ts,json,css,scss,md}'",
    zip: "npm run build && node src/zip.js"
  },
  dependencies: {
    "@radix-ui/react-slot": "^1.0.2",
    "class-variance-authority": "^0.7.0",
    clsx: "^2.1.1",
    "lucide-react": "^0.263.0",
    react: "^18.2.0",
    "react-dom": "^18.2.0",
    "socket.io-client": "^4.7.2",
    "tailwind-merge": "^1.14.0"
  },
  devDependencies: {
    "@crxjs/vite-plugin": "^2.0.0-beta.26",
    "@types/chrome": "^0.0.246",
    "@types/react": "^18.2.28",
    "@types/react-dom": "^18.2.13",
    "@vitejs/plugin-react": "^4.1.0",
    autoprefixer: "^10.4.0",
    gulp: "^5.0.0",
    "gulp-zip": "^6.0.0",
    postcss: "^8.4.0",
    prettier: "^3.0.3",
    tailwindcss: "^3.4.0",
    typescript: "^5.2.2",
    vite: "^5.4.10"
  },
  packageManager: "pnpm@10.18.2+sha512.9fb969fa749b3ade6035e0f109f0b8a60b5d08a1a87fdf72e337da90dcc93336e2280ca4e44f2358a649b83c17959e9993e777c2080879f3801e6f0d999ad3dd"
};

// src/manifest.ts
var isDev = process.env.NODE_ENV == "development";
var manifest_default = defineManifest({
  name: `${package_default.displayName || package_default.name}${isDev ? ` \u27A1\uFE0F Dev` : ""}`,
  description: package_default.description,
  version: package_default.version,
  manifest_version: 3,
  icons: {
    // @ts-ignore
    16: "img/icon16.png",
    // @ts-ignore
    32: "img/icon32.png",
    // @ts-ignore
    48: "img/icon48.png",
    // @ts-ignore
    128: "img/icon128.png"
  },
  action: {
    // @ts-ignore
    default_title: "Click to open Browser.AI Side Panel",
    // @ts-ignore
    default_icon: "img/icon48.png"
  },
  // @ts-ignore
  options_page: "options.html",
  // @ts-ignore
  devtools_page: "devtools.html",
  background: {
    // @ts-ignore
    service_worker: "src/background/index.ts",
    type: "module"
  },
  side_panel: {
    default_path: "sidepanel.html"
  },
  // @ts-ignore
  content_scripts: [
    {
      matches: ["<all_urls>"],
      // @ts-ignore
      js: ["src/content/index.tsx"],
      // @ts-ignore
      run_at: "document_end"
    }
  ],
  // @ts-ignore
  web_accessible_resources: [
    {
      resources: ["img/icon16.png", "img/icon32.png", "img/icon48.png", "img/icon128.png"],
      matches: []
    }
  ],
  permissions: ["sidePanel", "storage", "debugger", "tabs", "activeTab", "scripting"],
  // @ts-ignore
  host_permissions: ["<all_urls>"]
});

// vite.config.ts
var vite_config_default = defineConfig(({ mode }) => {
  const isProduction = mode === "production";
  return {
    base: "./",
    // Use relative paths for assets
    build: {
      emptyOutDir: true,
      outDir: "build",
      rollupOptions: {
        output: {
          chunkFileNames: "assets/chunk-[hash].js"
        }
      }
    },
    server: isProduction ? void 0 : {
      port: 5173,
      strictPort: true,
      hmr: {
        port: 5173
      }
    },
    plugins: [crx({ manifest: manifest_default }), react()]
  };
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiLCAic3JjL21hbmlmZXN0LnRzIiwgInBhY2thZ2UuanNvbiJdLAogICJzb3VyY2VzQ29udGVudCI6IFsiY29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2Rpcm5hbWUgPSBcIkU6XFxcXFByb2plY3RzXFxcXFByb2plY3RzXFxcXEJyb3dzZXIuQUlcXFxcQnJvd3Nlci5BSVxcXFxicm93c2VyX2FpX2V4dGVuc2lvblxcXFxicm93c2VfYWlcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfZmlsZW5hbWUgPSBcIkU6XFxcXFByb2plY3RzXFxcXFByb2plY3RzXFxcXEJyb3dzZXIuQUlcXFxcQnJvd3Nlci5BSVxcXFxicm93c2VyX2FpX2V4dGVuc2lvblxcXFxicm93c2VfYWlcXFxcdml0ZS5jb25maWcudHNcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfaW1wb3J0X21ldGFfdXJsID0gXCJmaWxlOi8vL0U6L1Byb2plY3RzL1Byb2plY3RzL0Jyb3dzZXIuQUkvQnJvd3Nlci5BSS9icm93c2VyX2FpX2V4dGVuc2lvbi9icm93c2VfYWkvdml0ZS5jb25maWcudHNcIjtpbXBvcnQgeyBkZWZpbmVDb25maWcgfSBmcm9tICd2aXRlJ1xyXG5pbXBvcnQgeyBjcnggfSBmcm9tICdAY3J4anMvdml0ZS1wbHVnaW4nXHJcbmltcG9ydCByZWFjdCBmcm9tICdAdml0ZWpzL3BsdWdpbi1yZWFjdCdcclxuXHJcbmltcG9ydCBtYW5pZmVzdCBmcm9tICcuL3NyYy9tYW5pZmVzdCdcclxuXHJcbi8vIGh0dHBzOi8vdml0ZWpzLmRldi9jb25maWcvXHJcbmV4cG9ydCBkZWZhdWx0IGRlZmluZUNvbmZpZygoeyBtb2RlIH0pID0+IHtcclxuICBjb25zdCBpc1Byb2R1Y3Rpb24gPSBtb2RlID09PSAncHJvZHVjdGlvbidcclxuXHJcbiAgcmV0dXJuIHtcclxuICAgIGJhc2U6ICcuLycsIC8vIFVzZSByZWxhdGl2ZSBwYXRocyBmb3IgYXNzZXRzXHJcbiAgICBidWlsZDoge1xyXG4gICAgICBlbXB0eU91dERpcjogdHJ1ZSxcclxuICAgICAgb3V0RGlyOiAnYnVpbGQnLFxyXG4gICAgICByb2xsdXBPcHRpb25zOiB7XHJcbiAgICAgICAgb3V0cHV0OiB7XHJcbiAgICAgICAgICBjaHVua0ZpbGVOYW1lczogJ2Fzc2V0cy9jaHVuay1baGFzaF0uanMnLFxyXG4gICAgICAgIH0sXHJcbiAgICAgIH0sXHJcbiAgICB9LFxyXG4gICAgc2VydmVyOiBpc1Byb2R1Y3Rpb25cclxuICAgICAgPyB1bmRlZmluZWRcclxuICAgICAgOiB7XHJcbiAgICAgICAgICBwb3J0OiA1MTczLFxyXG4gICAgICAgICAgc3RyaWN0UG9ydDogdHJ1ZSxcclxuICAgICAgICAgIGhtcjoge1xyXG4gICAgICAgICAgICBwb3J0OiA1MTczLFxyXG4gICAgICAgICAgfSxcclxuICAgICAgICB9LFxyXG4gICAgcGx1Z2luczogW2NyeCh7IG1hbmlmZXN0IH0pLCByZWFjdCgpXSxcclxuICB9XHJcbn0pXHJcbiIsICJjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfZGlybmFtZSA9IFwiRTpcXFxcUHJvamVjdHNcXFxcUHJvamVjdHNcXFxcQnJvd3Nlci5BSVxcXFxCcm93c2VyLkFJXFxcXGJyb3dzZXJfYWlfZXh0ZW5zaW9uXFxcXGJyb3dzZV9haVxcXFxzcmNcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfZmlsZW5hbWUgPSBcIkU6XFxcXFByb2plY3RzXFxcXFByb2plY3RzXFxcXEJyb3dzZXIuQUlcXFxcQnJvd3Nlci5BSVxcXFxicm93c2VyX2FpX2V4dGVuc2lvblxcXFxicm93c2VfYWlcXFxcc3JjXFxcXG1hbmlmZXN0LnRzXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ltcG9ydF9tZXRhX3VybCA9IFwiZmlsZTovLy9FOi9Qcm9qZWN0cy9Qcm9qZWN0cy9Ccm93c2VyLkFJL0Jyb3dzZXIuQUkvYnJvd3Nlcl9haV9leHRlbnNpb24vYnJvd3NlX2FpL3NyYy9tYW5pZmVzdC50c1wiO2ltcG9ydCB7IGRlZmluZU1hbmlmZXN0IH0gZnJvbSAnQGNyeGpzL3ZpdGUtcGx1Z2luJ1xyXG5pbXBvcnQgcGFja2FnZURhdGEgZnJvbSAnLi4vcGFja2FnZS5qc29uJ1xyXG5cclxuLy9AdHMtaWdub3JlXHJcbmNvbnN0IGlzRGV2ID0gcHJvY2Vzcy5lbnYuTk9ERV9FTlYgPT0gJ2RldmVsb3BtZW50J1xyXG5cclxuZXhwb3J0IGRlZmF1bHQgZGVmaW5lTWFuaWZlc3Qoe1xyXG4gIG5hbWU6IGAke3BhY2thZ2VEYXRhLmRpc3BsYXlOYW1lIHx8IHBhY2thZ2VEYXRhLm5hbWV9JHtpc0RldiA/IGAgXHUyN0ExXHVGRTBGIERldmAgOiAnJ31gLFxyXG4gIGRlc2NyaXB0aW9uOiBwYWNrYWdlRGF0YS5kZXNjcmlwdGlvbixcclxuICB2ZXJzaW9uOiBwYWNrYWdlRGF0YS52ZXJzaW9uLFxyXG4gIG1hbmlmZXN0X3ZlcnNpb246IDMsXHJcbiAgaWNvbnM6IHtcclxuICAgIC8vIEB0cy1pZ25vcmVcclxuICAgIDE2OiAnaW1nL2ljb24xNi5wbmcnLFxyXG4gICAgLy8gQHRzLWlnbm9yZVxyXG4gICAgMzI6ICdpbWcvaWNvbjMyLnBuZycsXHJcbiAgICAvLyBAdHMtaWdub3JlXHJcbiAgICA0ODogJ2ltZy9pY29uNDgucG5nJyxcclxuICAgIC8vIEB0cy1pZ25vcmVcclxuICAgIDEyODogJ2ltZy9pY29uMTI4LnBuZycsXHJcbiAgfSxcclxuICBhY3Rpb246IHtcclxuICAgIC8vIEB0cy1pZ25vcmVcclxuICAgIGRlZmF1bHRfdGl0bGU6ICdDbGljayB0byBvcGVuIEJyb3dzZXIuQUkgU2lkZSBQYW5lbCcsXHJcbiAgICAvLyBAdHMtaWdub3JlXHJcbiAgICBkZWZhdWx0X2ljb246ICdpbWcvaWNvbjQ4LnBuZycsXHJcbiAgfSxcclxuICAvLyBAdHMtaWdub3JlXHJcbiAgb3B0aW9uc19wYWdlOiAnb3B0aW9ucy5odG1sJyxcclxuICAvLyBAdHMtaWdub3JlXHJcbiAgZGV2dG9vbHNfcGFnZTogJ2RldnRvb2xzLmh0bWwnLFxyXG4gIGJhY2tncm91bmQ6IHtcclxuICAgIC8vIEB0cy1pZ25vcmVcclxuICAgIHNlcnZpY2Vfd29ya2VyOiAnc3JjL2JhY2tncm91bmQvaW5kZXgudHMnLFxyXG4gICAgdHlwZTogJ21vZHVsZScsXHJcbiAgfSxcclxuICBzaWRlX3BhbmVsOiB7XHJcbiAgICBkZWZhdWx0X3BhdGg6ICdzaWRlcGFuZWwuaHRtbCcsXHJcbiAgfSxcclxuICAvLyBAdHMtaWdub3JlXHJcbiAgY29udGVudF9zY3JpcHRzOiBbXHJcbiAgICB7XHJcbiAgICAgIG1hdGNoZXM6IFsnPGFsbF91cmxzPiddLFxyXG4gICAgICAvLyBAdHMtaWdub3JlXHJcbiAgICAgIGpzOiBbJ3NyYy9jb250ZW50L2luZGV4LnRzeCddLFxyXG4gICAgICAvLyBAdHMtaWdub3JlXHJcbiAgICAgIHJ1bl9hdDogJ2RvY3VtZW50X2VuZCcsXHJcbiAgICB9LFxyXG4gIF0sXHJcbiAgLy8gQHRzLWlnbm9yZVxyXG4gIHdlYl9hY2Nlc3NpYmxlX3Jlc291cmNlczogW1xyXG4gICAge1xyXG4gICAgICByZXNvdXJjZXM6IFsnaW1nL2ljb24xNi5wbmcnLCAnaW1nL2ljb24zMi5wbmcnLCAnaW1nL2ljb240OC5wbmcnLCAnaW1nL2ljb24xMjgucG5nJ10sXHJcbiAgICAgIG1hdGNoZXM6IFtdLFxyXG4gICAgfSxcclxuICBdLFxyXG4gIHBlcm1pc3Npb25zOiBbJ3NpZGVQYW5lbCcsICdzdG9yYWdlJywgJ2RlYnVnZ2VyJywgJ3RhYnMnLCAnYWN0aXZlVGFiJywgJ3NjcmlwdGluZyddLFxyXG4gIC8vIEB0cy1pZ25vcmVcclxuICBob3N0X3Blcm1pc3Npb25zOiBbJzxhbGxfdXJscz4nXSxcclxufSlcclxuIiwgIntcclxuICBcIm5hbWVcIjogXCJicm93c2VfYWlcIixcclxuICBcImRpc3BsYXlOYW1lXCI6IFwiYnJvd3NlX2FpXCIsXHJcbiAgXCJ2ZXJzaW9uXCI6IFwiMC4wLjBcIixcclxuICBcImF1dGhvclwiOiBcIioqXCIsXHJcbiAgXCJkZXNjcmlwdGlvblwiOiBcIlwiLFxyXG4gIFwidHlwZVwiOiBcIm1vZHVsZVwiLFxyXG4gIFwibGljZW5zZVwiOiBcIk1JVFwiLFxyXG4gIFwia2V5d29yZHNcIjogW1xyXG4gICAgXCJjaHJvbWUtZXh0ZW5zaW9uXCIsXHJcbiAgICBcInJlYWN0XCIsXHJcbiAgICBcInZpdGVcIixcclxuICAgIFwiY3JlYXRlLWNocm9tZS1leHRcIlxyXG4gIF0sXHJcbiAgXCJlbmdpbmVzXCI6IHtcclxuICAgIFwibm9kZVwiOiBcIj49MTQuMTguMFwiXHJcbiAgfSxcclxuICBcInNjcmlwdHNcIjoge1xyXG4gICAgXCJkZXZcIjogXCJ2aXRlXCIsXHJcbiAgICBcImJ1aWxkXCI6IFwidHNjICYmIHZpdGUgYnVpbGRcIixcclxuICAgIFwicHJldmlld1wiOiBcInZpdGUgcHJldmlld1wiLFxyXG4gICAgXCJmbXRcIjogXCJwcmV0dGllciAtLXdyaXRlICcqKi8qLnt0c3gsdHMsanNvbixjc3Msc2NzcyxtZH0nXCIsXHJcbiAgICBcInppcFwiOiBcIm5wbSBydW4gYnVpbGQgJiYgbm9kZSBzcmMvemlwLmpzXCJcclxuICB9LFxyXG4gIFwiZGVwZW5kZW5jaWVzXCI6IHtcclxuICAgIFwiQHJhZGl4LXVpL3JlYWN0LXNsb3RcIjogXCJeMS4wLjJcIixcclxuICAgIFwiY2xhc3MtdmFyaWFuY2UtYXV0aG9yaXR5XCI6IFwiXjAuNy4wXCIsXHJcbiAgICBcImNsc3hcIjogXCJeMi4xLjFcIixcclxuICAgIFwibHVjaWRlLXJlYWN0XCI6IFwiXjAuMjYzLjBcIixcclxuICAgIFwicmVhY3RcIjogXCJeMTguMi4wXCIsXHJcbiAgICBcInJlYWN0LWRvbVwiOiBcIl4xOC4yLjBcIixcclxuICAgIFwic29ja2V0LmlvLWNsaWVudFwiOiBcIl40LjcuMlwiLFxyXG4gICAgXCJ0YWlsd2luZC1tZXJnZVwiOiBcIl4xLjE0LjBcIlxyXG4gIH0sXHJcbiAgXCJkZXZEZXBlbmRlbmNpZXNcIjoge1xyXG4gICAgXCJAY3J4anMvdml0ZS1wbHVnaW5cIjogXCJeMi4wLjAtYmV0YS4yNlwiLFxyXG4gICAgXCJAdHlwZXMvY2hyb21lXCI6IFwiXjAuMC4yNDZcIixcclxuICAgIFwiQHR5cGVzL3JlYWN0XCI6IFwiXjE4LjIuMjhcIixcclxuICAgIFwiQHR5cGVzL3JlYWN0LWRvbVwiOiBcIl4xOC4yLjEzXCIsXHJcbiAgICBcIkB2aXRlanMvcGx1Z2luLXJlYWN0XCI6IFwiXjQuMS4wXCIsXHJcbiAgICBcImF1dG9wcmVmaXhlclwiOiBcIl4xMC40LjBcIixcclxuICAgIFwiZ3VscFwiOiBcIl41LjAuMFwiLFxyXG4gICAgXCJndWxwLXppcFwiOiBcIl42LjAuMFwiLFxyXG4gICAgXCJwb3N0Y3NzXCI6IFwiXjguNC4wXCIsXHJcbiAgICBcInByZXR0aWVyXCI6IFwiXjMuMC4zXCIsXHJcbiAgICBcInRhaWx3aW5kY3NzXCI6IFwiXjMuNC4wXCIsXHJcbiAgICBcInR5cGVzY3JpcHRcIjogXCJeNS4yLjJcIixcclxuICAgIFwidml0ZVwiOiBcIl41LjQuMTBcIlxyXG4gIH0sXHJcbiAgXCJwYWNrYWdlTWFuYWdlclwiOiBcInBucG1AMTAuMTguMitzaGE1MTIuOWZiOTY5ZmE3NDliM2FkZTYwMzVlMGYxMDlmMGI4YTYwYjVkMDhhMWE4N2ZkZjcyZTMzN2RhOTBkY2M5MzMzNmUyMjgwY2E0ZTQ0ZjIzNThhNjQ5YjgzYzE3OTU5ZTk5OTNlNzc3YzIwODA4NzlmMzgwMWU2ZjBkOTk5YWQzZGRcIlxyXG59XHJcbiJdLAogICJtYXBwaW5ncyI6ICI7QUFBMlosU0FBUyxvQkFBb0I7QUFDeGIsU0FBUyxXQUFXO0FBQ3BCLE9BQU8sV0FBVzs7O0FDRmlaLFNBQVMsc0JBQXNCOzs7QUNBbGM7QUFBQSxFQUNFLE1BQVE7QUFBQSxFQUNSLGFBQWU7QUFBQSxFQUNmLFNBQVc7QUFBQSxFQUNYLFFBQVU7QUFBQSxFQUNWLGFBQWU7QUFBQSxFQUNmLE1BQVE7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
