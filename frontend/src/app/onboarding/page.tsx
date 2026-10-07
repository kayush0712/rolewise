import { auth, clerkClient } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import { OnboardingClient } from "./onboarding-client";

type Props = {
  searchParams?: Promise<{ [key: string]: string | string[] | undefined }>;
};

export default async function OnboardingPage(props: Props) {
  const { userId } = await auth();

  if (!userId) {
    redirect("/");
  }

  const client = await clerkClient();
  const user = await client.users.getUser(userId);

  // If already onboarded and not forced, send them to dashboard
  const searchParams = await props.searchParams;
  if (user.publicMetadata?.onboardingComplete && searchParams?.force !== "true") {
    redirect("/roles");
  }

  return (
    <div className="min-h-screen bg-rw-bg flex items-center justify-center p-4 sm:p-8">
      <div className="w-full max-w-2xl relative z-10">
        <OnboardingClient />
      </div>
    </div>
  );
}
