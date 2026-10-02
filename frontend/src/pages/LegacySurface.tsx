import { useLocation } from "react-router-dom";
import { LegacyLayout } from "../legacy/AppLegacy";

export function LegacySurface() {
  const location = useLocation();
  return <LegacyLayout path={location.pathname} />;
}
