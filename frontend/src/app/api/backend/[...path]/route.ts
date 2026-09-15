import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

const ACCESS_COOKIE = "serenity_access";
const REFRESH_COOKIE = "serenity_refresh";
const BACKEND_API_BASE_URL =
  process.env.BACKEND_API_BASE_URL ?? "http://localhost:8000/api/v1";

type HandlerContext = {
  params: Promise<{ path: string[] }>;
};

const cookieOptions = {
  httpOnly: true,
  secure: process.env.NODE_ENV === "production",
  sameSite: "strict" as const,
  path: "/",
  priority: "high" as const,
};

function safeBackendUrl(path: string[], request: NextRequest) {
  if (
    path.length === 0 ||
    path.some((segment) => !segment || segment === "." || segment === "..")
  ) {
    return null;
  }

  const encodedPath = path.map(encodeURIComponent).join("/");
  const url = new URL(
    `${BACKEND_API_BASE_URL.replace(/\/$/, "")}/${encodedPath}/`
  );
  request.nextUrl.searchParams.forEach((value, key) => {
    url.searchParams.append(key, value);
  });
  return url;
}

async function refreshAccessToken(refreshToken: string) {
  const response = await fetch(
    `${BACKEND_API_BASE_URL.replace(/\/$/, "")}/auth/token/refresh/`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: refreshToken }),
      cache: "no-store",
    }
  );
  if (!response.ok) return null;

  const data = (await response.json()) as {
    access?: string;
    refresh?: string;
  };
  return data.access ? data : null;
}

async function proxyRequest(
  request: NextRequest,
  context: HandlerContext
) {
  const { path } = await context.params;
  const backendUrl = safeBackendUrl(path, request);
  if (!backendUrl) {
    return NextResponse.json({ error: "Invalid API path." }, { status: 400 });
  }

  const route = path.join("/");
  const isLogin = route === "auth/login";
  const isLogout = route === "auth/logout";
  const cookieStore = await cookies();
  let accessToken = cookieStore.get(ACCESS_COOKIE)?.value;
  const refreshToken = cookieStore.get(REFRESH_COOKIE)?.value;

  let body: ArrayBuffer | string | undefined;
  if (!["GET", "HEAD"].includes(request.method)) {
    body = await request.arrayBuffer();
  }
  if (isLogout) {
    body = JSON.stringify({ refresh: refreshToken ?? "" });
  }

  const send = (token?: string) => {
    const headers = new Headers();
    const contentType = request.headers.get("content-type");
    if (contentType) headers.set("Content-Type", contentType);
    headers.set("Accept", request.headers.get("accept") ?? "application/json");
    const requestId = request.headers.get("x-request-id");
    if (requestId) headers.set("X-Request-ID", requestId);
    if (token && !isLogin) headers.set("Authorization", `Bearer ${token}`);

    return fetch(backendUrl, {
      method: request.method,
      headers,
      body,
      cache: "no-store",
      redirect: "manual",
    });
  };

  let backendResponse = await send(accessToken);

  if (
    backendResponse.status === 401 &&
    refreshToken &&
    !isLogin &&
    !isLogout
  ) {
    const refreshedTokens = await refreshAccessToken(refreshToken);
    accessToken = refreshedTokens?.access;
    if (accessToken) {
      cookieStore.set(ACCESS_COOKIE, accessToken, {
        ...cookieOptions,
        maxAge: 15 * 60,
      });
      if (refreshedTokens?.refresh) {
        cookieStore.set(REFRESH_COOKIE, refreshedTokens.refresh, {
          ...cookieOptions,
          maxAge: 7 * 24 * 60 * 60,
        });
      }
      backendResponse = await send(accessToken);
    }
  }

  if (isLogin && backendResponse.ok) {
    const data = (await backendResponse.json()) as {
      tokens?: { access?: string; refresh?: string };
      user?: unknown;
    };
    if (!data.tokens?.access || !data.tokens.refresh) {
      return NextResponse.json(
        { error: "The authentication server returned an invalid response." },
        { status: 502 }
      );
    }
    cookieStore.set(ACCESS_COOKIE, data.tokens.access, {
      ...cookieOptions,
      maxAge: 15 * 60,
    });
    cookieStore.set(REFRESH_COOKIE, data.tokens.refresh, {
      ...cookieOptions,
      maxAge: 7 * 24 * 60 * 60,
    });
    return NextResponse.json({ user: data.user });
  }

  if (isLogout) {
    cookieStore.delete(ACCESS_COOKIE);
    cookieStore.delete(REFRESH_COOKIE);
  } else if (backendResponse.status === 401) {
    cookieStore.delete(ACCESS_COOKIE);
    cookieStore.delete(REFRESH_COOKIE);
  }

  const responseHeaders = new Headers();
  for (const header of [
    "content-type",
    "content-disposition",
    "x-request-id",
  ]) {
    const value = backendResponse.headers.get(header);
    if (value) responseHeaders.set(header, value);
  }

  return new NextResponse(await backendResponse.arrayBuffer(), {
    status: backendResponse.status,
    headers: responseHeaders,
  });
}

export const dynamic = "force-dynamic";

export function GET(request: NextRequest, context: HandlerContext) {
  return proxyRequest(request, context);
}

export function POST(request: NextRequest, context: HandlerContext) {
  return proxyRequest(request, context);
}

export function PUT(request: NextRequest, context: HandlerContext) {
  return proxyRequest(request, context);
}

export function PATCH(request: NextRequest, context: HandlerContext) {
  return proxyRequest(request, context);
}

export function DELETE(request: NextRequest, context: HandlerContext) {
  return proxyRequest(request, context);
}

