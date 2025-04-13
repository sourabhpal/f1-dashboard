import { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import Navbar from '../components/Navbar';
import YearSelector from '../components/YearSelector';

export default function FastF1() {
    const [year, setYear] = useState(new Date().getFullYear());
    const [drivers, setDrivers] = useState([]);
    const [constructors, setConstructors] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                // Fetch drivers data
                const driversResponse = await axios.get(`https://ergast.com/api/f1/${year}/drivers.json`);
                setDrivers(driversResponse.data.MRData.DriverTable.Drivers);

                // Fetch constructors data
                const constructorsResponse = await axios.get(`https://ergast.com/api/f1/${year}/constructors.json`);
                setConstructors(constructorsResponse.data.MRData.ConstructorTable.Constructors);

                setLoading(false);
            } catch (err) {
                setError('Failed to fetch data');
                setLoading(false);
            }
        };

        fetchData();
    }, [year]);

    if (loading) {
        return (
            <Layout>
                <Navbar />
                <div className="container mx-auto px-4 py-8">
                    <div className="flex justify-center items-center h-64">
                        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-red-600"></div>
                    </div>
                </div>
            </Layout>
        );
    }

    if (error) {
        return (
            <Layout>
                <Navbar />
                <div className="container mx-auto px-4 py-8">
                    <div className="text-center text-red-600">{error}</div>
                </div>
            </Layout>
        );
    }

    return (
        <Layout>
            <Navbar />
            <div className="container mx-auto px-4 py-8">
                <div className="flex justify-between items-center mb-8">
                    <h1 className="text-3xl font-bold text-gray-900">FastF1 Data</h1>
                    <YearSelector year={year} setYear={setYear} />
                </div>

                {/* Drivers Section */}
                <div className="mb-12">
                    <h2 className="text-2xl font-semibold mb-4 text-gray-800">Drivers</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {drivers.map((driver) => (
                            <div
                                key={driver.driverId}
                                className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
                            >
                                <div className="flex items-center space-x-4">
                                    <div className="flex-1">
                                        <h3 className="text-xl font-semibold text-gray-900">
                                            {driver.givenName} {driver.familyName}
                                        </h3>
                                        <p className="text-gray-600">Number: {driver.permanentNumber || 'N/A'}</p>
                                        <p className="text-gray-600">Nationality: {driver.nationality}</p>
                                        <a
                                            href={driver.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-red-600 hover:text-red-800 mt-2 inline-block"
                                        >
                                            View Profile
                                        </a>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Constructors Section */}
                <div>
                    <h2 className="text-2xl font-semibold mb-4 text-gray-800">Constructors</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {constructors.map((constructor) => (
                            <div
                                key={constructor.constructorId}
                                className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
                            >
                                <div className="flex items-center space-x-4">
                                    <div className="flex-1">
                                        <h3 className="text-xl font-semibold text-gray-900">
                                            {constructor.name}
                                        </h3>
                                        <p className="text-gray-600">Nationality: {constructor.nationality}</p>
                                        <a
                                            href={constructor.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-red-600 hover:text-red-800 mt-2 inline-block"
                                        >
                                            View Profile
                                        </a>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </Layout>
    );
} 