import type { AppProps } from 'next/app';
import { SupabaseProvider } from '../providers/SupabaseProvider';
import '../styles/globals.css';

function MyApp({ Component, pageProps }: AppProps) {
  return (
    <SupabaseProvider>
      <Component {...pageProps} />
    </SupabaseProvider>
  );
}

export default MyApp;
