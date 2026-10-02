import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.moduleiq.app",
  appName: "ModuleIQ",
  webDir: "dist",
  server: { androidScheme: "http", cleartext: true }
};

export default config;
