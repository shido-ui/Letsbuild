import type { CapacitorConfig } from "@capacitor/cli";

const allowCleartext = process.env.CAPACITOR_ALLOW_CLEARTEXT === "true";

const config: CapacitorConfig = {
  appId: "com.moduleiq.app",
  appName: "ModuleIQ",
  webDir: "dist",
  server: {
    androidScheme: "https",
    cleartext: allowCleartext,
  },
};

export default config;
