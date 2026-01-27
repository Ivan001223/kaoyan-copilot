import React from 'react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from 'recharts';
import { RadarStat } from '../services/api';

interface RadarChartProps {
    data: RadarStat[];
}

export const AbilityRadar: React.FC<RadarChartProps> = ({ data }) => {
    if (!data || data.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-[300px] bg-gray-50 rounded-lg border border-dashed border-gray-300">
                <div className="text-4xl mb-2">📊</div>
                <div className="text-gray-500">暂无能力模型数据</div>
                <div className="text-xs text-gray-400 mt-1">请先去刷题积累数据</div>
            </div>
        );
    }

    return (
        <div className="w-full h-[350px] bg-white p-4 rounded-lg shadow-sm border border-gray-100">
            <h3 className="text-sm font-bold text-gray-700 mb-2">能力雷达图</h3>
            <ResponsiveContainer width="100%" height="90%">
                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="tag" tick={{ fontSize: 12, fill: '#666' }} />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} />
                    <Radar
                        name="掌握度"
                        dataKey="score"
                        stroke="#2563eb"
                        fill="#3b82f6"
                        fillOpacity={0.5}
                    />
                    <Tooltip 
                        contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                        itemStyle={{ color: '#2563eb', fontWeight: 'bold' }}
                    />
                </RadarChart>
            </ResponsiveContainer>
        </div>
    );
};
