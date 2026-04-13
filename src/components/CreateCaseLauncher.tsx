'use client';

import { useRouter, useSearchParams, usePathname } from 'next/navigation';
import CreateCaseModal from './CreateCaseModal';
import { MedicalCase } from '@/types';

export default function CreateCaseLauncher() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const isOpen = searchParams.get('new') === '1';

  const close = () => {
    const params = new URLSearchParams(searchParams);
    params.delete('new');
    const qs = params.toString();
    router.push(qs ? `${pathname}?${qs}` : pathname);
  };

  const handleCreated = (newCase: MedicalCase) => {
    close();
    router.push(`/cases/${newCase.id}`);
  };

  if (!isOpen) return null;
  return <CreateCaseModal onClose={close} onCreate={handleCreated} />;
}
