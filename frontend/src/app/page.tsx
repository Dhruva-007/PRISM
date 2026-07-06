/**
 * PRISM root page.
 *
 * Redirects to the login page.
 * The dashboard layout handles redirect to overview after auth.
 */

import { redirect } from "next/navigation";
import { ROUTES } from "@/constants/routes";

export default function RootPage() {
  redirect(ROUTES.LOGIN);
}