import { Inter } from 'next/font/google';
import { Oxanium } from 'next/font/google';
import '../styles/globals.css'

const inter = Inter({ subsets: ['latin'] });
const oxanium = Oxanium({ 
  subsets: ['latin'],
  variable: '--font-oxanium',
});

function MyApp({ Component, pageProps }) {
  return (
    <main className={`${inter.className} ${oxanium.variable}`}>
      <Component {...pageProps} />
    </main>
  );
}

export default MyApp 