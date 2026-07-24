import { NextResponse, type NextRequest } from 'next/server'

export function proxy(request: NextRequest) {
  const isAuthenticated = request.cookies.get('firebase-auth')?.value === 'true'

  const protectedPaths = ['/dashboard', '/profile', '/bookmarks', '/applications', '/calendar', '/leaderboard', '/team-finder', '/notifications', '/opportunities']
  const isProtectedPath = protectedPaths.some(path => request.nextUrl.pathname.startsWith(path))

  if (isProtectedPath && !isAuthenticated) {
    const url = request.nextUrl.clone()
    url.pathname = '/login'
    const redirectPath = request.nextUrl.pathname
    if (redirectPath.startsWith('/') && !redirectPath.startsWith('//')) {
      url.searchParams.set('redirect', redirectPath)
    }
    return NextResponse.redirect(url)
  }

  const authPaths = ['/login', '/signup', '/get-started']
  const isAuthPath = authPaths.some(path => request.nextUrl.pathname.startsWith(path))

  if (isAuthPath && isAuthenticated) {
    const url = request.nextUrl.clone()
    url.pathname = '/dashboard'
    return NextResponse.redirect(url)
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)'],
}
