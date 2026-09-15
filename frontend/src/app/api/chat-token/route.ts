import { cookies } from "next/headers";
import { NextResponse } from "next/server";

const ACCESS_COOKIE = "serenity_access";

/**
 * Bridges the existing HTTP-only session cookie to the browser's WebSocket
 * constructor. The token stays in component memory and is never persisted or
 * logged by the frontend.
 */
export async function GET() {
  const cookieStore = await cookies();
  return NextResponse.json(
    { token: cookieStore.get(ACCESS_COOKIE)?.value ?? null },
    { headers: { "Cache-Control": "no-store" } }
  );
}
