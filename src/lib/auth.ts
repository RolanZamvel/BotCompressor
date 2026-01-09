import { NextAuthOptions } from "next-auth"
import { getServerSession as getNextAuthServerSession } from "next-auth"

export const authOptions: NextAuthOptions = {
  providers: [
    Credentials({
      name: "Dashboard Login",
      credentials: {
        username: { label: "Usuario", type: "text" },
        password: { label: "Contraseña", type: "password" }
      },
      async authorize(credentials) {
        // Autenticación simple para demo
        // EN PRODUCCIÓN: Implementar autenticación real (base de datos, LDAP, etc.)
        const validUsers = [
          { id: "1", username: "admin", password: "admin", name: "Administrador" },
          { id: "2", username: "user", password: "user", name: "Usuario" }
        ]

        const user = validUsers.find(
          u => u.username === credentials?.username && u.password === credentials?.password
        )

        if (user) {
          return {
            id: user.id,
            name: user.name,
            email: `${user.username}@botcompressor.local`
          }
        }

        throw new Error("Usuario o contraseña incorrectos")
      }
    })
  ],
  pages: {
    signIn: '/login',
    error: '/login',
  },
  session: {
    strategy: "jwt",
    maxAge: 30 * 24 * 60 * 60, // 30 días
  },
  secret: process.env.NEXTAUTH_SECRET || "your-secret-key-change-this-in-production",
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id
      }
      return token
    },
    async session({ session, token }) {
      if (session.user) {
        (session.user as any).id = token.id
      }
      return session
    },
  },
}

export const getServerSession = async () => {
  return await getNextAuthServerSession(authOptions)
}

export default authOptions
