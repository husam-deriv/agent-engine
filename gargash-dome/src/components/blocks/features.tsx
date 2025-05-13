'use client'
import { Activity, Map as MapIcon, MessageCircle } from 'lucide-react'
import DottedMap from 'dotted-map'
import { Area, AreaChart, CartesianGrid } from 'recharts'
import { type ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart'

export function Features() {
    return (
        <section className="px-4 py-16 md:py-32 bg-black text-white">
            <div className="mx-auto grid max-w-5xl border border-gray-800 md:grid-cols-2 rounded-xl overflow-hidden">
                <div className="bg-[#111111]">
                    <div className="p-6 sm:p-12">
                        <span className="text-gray-400 flex items-center gap-2">
                            <MapIcon className="size-4" />
                            Unified Customer Profiles
                        </span>

                        <p className="mt-8 text-2xl font-semibold text-white">Complete cross-pillar view of every customer interaction across Automotive, Financial Services, and Real Estate.</p>
                    </div>

                    <div aria-hidden className="relative">
                        <div className="absolute inset-0 z-10 m-auto size-fit">
                            <div className="rounded-[--radius] bg-[#191919] z-[1] relative flex size-fit w-fit items-center gap-2 border border-gray-800 px-3 py-1 text-xs font-medium shadow-md shadow-black/5">
                                <span className="text-lg">🚗</span> John's car service appointment confirmed
                            </div>
                            <div className="rounded-[--radius] bg-[#141414] absolute inset-2 -bottom-2 mx-auto border border-gray-800 px-3 py-4 text-xs font-medium shadow-md shadow-black/5"></div>
                        </div>

                        <div className="relative overflow-hidden">
                            <div className="[background-image:radial-gradient(var(--tw-gradient-stops))] z-1 to-[#111111] absolute inset-0 from-transparent to-75%"></div>
                            <Map />
                        </div>
                    </div>
                </div>
                <div className="overflow-hidden border-t border-gray-800 bg-[#111111] p-6 sm:p-12 md:border-0 md:border-l">
                    <div className="relative z-10">
                        <span className="text-gray-400 flex items-center gap-2">
                            <MessageCircle className="size-4" />
                            Cross-Pillar Agent Communication
                        </span>

                        <p className="my-8 text-2xl font-semibold text-white">Seamless agent-to-agent orchestration to deliver integrated customer experiences across business units.</p>
                    </div>
                    <div aria-hidden className="flex flex-col gap-8">
                        <div>
                            <div className="flex items-center gap-2">
                                <span className="flex justify-center items-center size-5 rounded-full border border-gray-700">
                                    <span className="size-3 rounded-full bg-[#f60021]"/>
                                </span>
                                <span className="text-gray-400 text-xs">Automotive Agent</span>
                            </div>
                            <div className="rounded-[--radius] bg-[#191919] mt-1.5 w-3/5 border border-gray-800 p-3 text-xs text-gray-300">Customer ID #45892 requires service scheduling and has property interest from Real Estate.</div>
                        </div>

                        <div>
                            <div className="rounded-[--radius] mb-1 ml-auto w-3/5 bg-[#f60021]/20 border border-[#f60021]/30 p-3 text-xs text-white">Retrieving unified profile. Pre-approving financing options based on credit history and preparing property listings near service center location.</div>
                            <span className="text-gray-400 block text-right text-xs">Financial Agent</span>
                        </div>
                    </div>
                </div>
                <div className="col-span-full border-y border-gray-800 bg-gradient-to-r from-black via-[#111111] to-black p-12">
                    <p className="text-center text-4xl font-semibold lg:text-7xl text-white">Unified Gargash Experience</p>
                </div>
                <div className="relative col-span-full bg-[#111111]">
                    <div className="absolute z-10 max-w-lg px-6 pr-12 pt-6 md:px-12 md:pt-12">
                        <span className="text-gray-400 flex items-center gap-2">
                            <Activity className="size-4" />
                            Cross-Pillar Analytics
                        </span>

                        <p className="my-8 text-2xl font-semibold text-white">
                            Monitor customer journeys across all business units. <span className="text-gray-400">Identify cross-selling opportunities and optimize the unified experience.</span>
                        </p>
                    </div>
                    <MonitoringChart />
                </div>
            </div>
        </section>
    )
}

const map = new DottedMap({ height: 55, grid: 'diagonal' })

const points = map.getPoints()

const svgOptions = {
    backgroundColor: '#111111',
    color: 'rgba(255, 255, 255, 0.3)',
    radius: 0.15,
}

const Map = () => {
    const viewBox = `0 0 120 60`
    return (
        <svg viewBox={viewBox} style={{ background: svgOptions.backgroundColor }}>
            {points.map((point, index) => (
                <circle key={index} cx={point.x} cy={point.y} r={svgOptions.radius} fill={svgOptions.color} />
            ))}
        </svg>
    )
}

const chartConfig = {
    automotive: {
        label: 'Automotive',
        color: '#f60021',
    },
    realEstate: {
        label: 'Real Estate',
        color: '#60a5fa',
    },
} satisfies ChartConfig

const chartData = [
    { month: 'May', automotive: 56, realEstate: 224 },
    { month: 'June', automotive: 56, realEstate: 224 },
    { month: 'January', automotive: 126, realEstate: 252 },
    { month: 'February', automotive: 205, realEstate: 410 },
    { month: 'March', automotive: 200, realEstate: 126 },
    { month: 'April', automotive: 400, realEstate: 800 },
]

const MonitoringChart = () => {
    return (
        <ChartContainer className="h-120 aspect-auto md:h-96 text-gray-400" config={chartConfig}>
            <AreaChart
                accessibilityLayer
                data={chartData}
                margin={{
                    left: 0,
                    right: 0,
                }}>
                <defs>
                    <linearGradient id="fillAutomotive" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="var(--color-automotive)" stopOpacity={0.4} />
                        <stop offset="55%" stopColor="var(--color-automotive)" stopOpacity={0.1} />
                    </linearGradient>
                    <linearGradient id="fillRealEstate" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="var(--color-realEstate)" stopOpacity={0.4} />
                        <stop offset="55%" stopColor="var(--color-realEstate)" stopOpacity={0.1} />
                    </linearGradient>
                </defs>
                <CartesianGrid vertical={false} stroke="rgba(255,255,255,0.1)" />
                <ChartTooltip active cursor={false} content={<ChartTooltipContent className="bg-[#191919] border border-gray-800 text-white" />} />
                <Area strokeWidth={2} dataKey="realEstate" type="stepBefore" fill="url(#fillRealEstate)" fillOpacity={0.1} stroke="var(--color-realEstate)" stackId="a" />
                <Area strokeWidth={2} dataKey="automotive" type="stepBefore" fill="url(#fillAutomotive)" fillOpacity={0.1} stroke="var(--color-automotive)" stackId="a" />
            </AreaChart>
        </ChartContainer>
    )
}
