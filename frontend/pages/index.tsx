import Head from 'next/head';
import { NextPage } from 'next';
import FileUpload from '../components/FileUpload';

const Home: NextPage = () => {
  return (
    <>
      <Head>
        <title>Budget App</title>
        <meta name="description" content="Upload your bank statements and categorize transactions" />
      </Head>
      <main className="p-8">
        <h1 className="text-3xl font-bold">Budget Control</h1>
        <p className="text-gray-600 mt-2">Upload your CSV or Excel files to parse and store your transactions.</p>
        <FileUpload />
      </main>
    </>
  );
};

export default Home;