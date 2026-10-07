import { auth, clerkClient } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";

export default async function RolesLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { userId } = await auth();

  if (!userId) {
    redirect("/");
  }

  const client = await clerkClient();
  const user = await client.users.getUser(userId);

  if (!user.publicMetadata?.onboardingComplete) {
    redirect("/onboarding");
  }

  return <>{children}</>;
}
