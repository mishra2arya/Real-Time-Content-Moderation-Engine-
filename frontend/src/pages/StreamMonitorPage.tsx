import React, { useState } from 'react';
import { Radio, Search, Trash2, Filter } from 'lucide-react';
import { DecisionBadge } from '../components/DecisionBadge';
import { ModerationEvent, ModerationDecision } from '../types';

interface StreamMonitorPageProps {
  events: ModerationEvent[];
  onClearEvents: () => void;
}

export const StreamMonitorPage: React.FC<StreamMonitorPageProps> = ({ events, onClearEvents }) => {
  const [filterDecision, setFilterDecision] = useState<ModerationDecision | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEvent, setSelectedEvent] = useState<ModerationEvent | null>(null);

  const filteredEvents = events.filter((evt) => {
    if (filterDecision !== 'all' && evt.decision !== filterDecision) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        evt.text.toLowerCase().includes(q) ||
        evt.id.toLowerCase().includes(q) ||
        (evt.category && evt.category.toLowerCase().includes(q))
      );
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Stream Controls */}
      <div className="bg-[#1D1B22] border border-[#37333D] rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-[#FB7185]/10 border border-[#FB7185]/30">
            <Radio className="w-4 h-4 text-[#FB7185] animate-pulse" />
          </div>
          <div>
            <h2 className="text-sm font-bold uppercase tracking-wider text-[#F5F3F7]">
              Live Moderation Event Stream
            </h2>
            <p className="text-xs text-[#A8A3AF] font-mono">
              Capturing all inference verdicts evaluated through this session
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 w-full md:w-auto">
          {/* Search */}
          <div className="relative flex-1 md:w-56">
            <Search className="w-3.5 h-3.5 text-[#A8A3AF] absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search text or ID..."
              className="w-full bg-[#151419] border border-[#37333D] rounded-lg pl-8 pr-3 py-1.5 text-xs text-[#F5F3F7] placeholder-[#A8A3AF]/40 outline-none font-mono focus:border-[#A78BFA]"
            />
          </div>

          {/* Filter Dropdown */}
          <div className="flex items-center gap-1 bg-[#151419] border border-[#37333D] rounded-lg p-1 text-xs font-mono">
            <Filter className="w-3.5 h-3.5 text-[#A8A3AF] ml-1.5" />
            {(['all', 'allow', 'flag_review', 'block'] as const).map((d) => (
              <button
                key={d}
                onClick={() => setFilterDecision(d)}
                className={`px-2 py-0.5 rounded text-[11px] uppercase transition-colors ${
                  filterDecision === d
                    ? 'bg-[#242128] text-[#F5F3F7] font-bold'
                    : 'text-[#A8A3AF] hover:text-[#F5F3F7]'
                }`}
              >
                {d === 'all' ? 'All' : d === 'flag_review' ? 'Review' : d}
              </button>
            ))}
          </div>

          <button
            onClick={onClearEvents}
            disabled={events.length === 0}
            className="p-2 rounded-lg bg-[#151419] hover:bg-[#242128] border border-[#37333D] text-[#A8A3AF] hover:text-[#FB7185] transition-colors disabled:opacity-40"
            title="Clear all events"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Stream Table */}
      <div className="bg-[#1D1B22] border border-[#37333D] rounded-xl overflow-hidden">
        {filteredEvents.length === 0 ? (
          <div className="py-24 text-center space-y-2 text-xs font-mono text-[#A8A3AF]">
            <Radio className="w-8 h-8 text-[#A8A3AF]/40 mx-auto" />
            <p className="text-sm font-semibold text-[#F5F3F7]">No stream events match current filter</p>
            <p className="text-xs text-[#A8A3AF]/60">
              Submit moderation requests from the Sandbox or API to see live streaming entries.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-[#37333D] bg-[#151419] text-[#A8A3AF]">
                  <th className="py-3 px-4 font-semibold">TIMESTAMP</th>
                  <th className="py-3 px-4 font-semibold">DECISION</th>
                  <th className="py-3 px-4 font-semibold">LABEL</th>
                  <th className="py-3 px-4 font-semibold">TEXT PREVIEW</th>
                  <th className="py-3 px-4 font-semibold">CONFIDENCE</th>
                  <th className="py-3 px-4 font-semibold">CATEGORY</th>
                  <th className="py-3 px-4 font-semibold text-right">LATENCY</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#37333D]/40">
                {filteredEvents.map((evt) => (
                  <tr
                    key={evt.id}
                    onClick={() => setSelectedEvent(evt)}
                    className="hover:bg-[#242128] cursor-pointer transition-colors"
                  >
                    <td className="py-3 px-4 text-[#A8A3AF]">{evt.timestamp}</td>
                    <td className="py-3 px-4">
                      <DecisionBadge decision={evt.decision} size="sm" />
                    </td>
                    <td className="py-3 px-4 uppercase font-bold text-[#F5F3F7]">
                      {evt.label}
                    </td>
                    <td className="py-3 px-4 text-[#F5F3F7] max-w-md truncate" title={evt.text}>
                      {evt.text}
                    </td>
                    <td className="py-3 px-4 text-[#A78BFA] font-medium">
                      {(evt.confidence * 100).toFixed(1)}%
                    </td>
                    <td className="py-3 px-4">
                      {evt.category ? (
                        <span className="px-1.5 py-0.5 rounded text-[10px] uppercase bg-[#FB7185]/15 text-[#FB7185] border border-[#FB7185]/30">
                          {evt.category}
                        </span>
                      ) : (
                        <span className="text-[#34D399]">none</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right text-[#34D399] font-bold">
                      {evt.latencyMs.toFixed(1)} ms
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Selected Event Modal */}
      {selectedEvent && (
        <div
          className="fixed inset-0 bg-[#111014]/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => setSelectedEvent(null)}
        >
          <div
            className="bg-[#1D1B22] border border-[#37333D] rounded-xl max-w-lg w-full p-6 space-y-4 shadow-[0_0_30px_rgba(0,0,0,0.5)]"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-3 border-b border-[#37333D]">
              <span className="text-xs font-mono text-[#A8A3AF]">EVENT INSPECTOR</span>
              <DecisionBadge decision={selectedEvent.decision} />
            </div>

            <div className="space-y-3 text-xs font-mono">
              <div>
                <span className="text-[#A8A3AF] block text-[10px] mb-1">RAW CONTENT</span>
                <p className="p-3 rounded-lg bg-[#151419] border border-[#37333D] text-[#F5F3F7] font-sans text-sm">
                  {selectedEvent.text}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="p-2.5 rounded bg-[#151419] border border-[#37333D]/60">
                  <span className="text-[#A8A3AF] block text-[10px]">TIMESTAMP</span>
                  <span className="text-[#F5F3F7]">{selectedEvent.timestamp}</span>
                </div>
                <div className="p-2.5 rounded bg-[#151419] border border-[#37333D]/60">
                  <span className="text-[#A8A3AF] block text-[10px]">TOTAL LATENCY</span>
                  <span className="text-[#34D399] font-bold">{selectedEvent.latencyMs.toFixed(2)} ms</span>
                </div>
                <div className="p-2.5 rounded bg-[#151419] border border-[#37333D]/60">
                  <span className="text-[#A8A3AF] block text-[10px]">CONFIDENCE</span>
                  <span className="text-[#A78BFA] font-bold">{(selectedEvent.confidence * 100).toFixed(2)}%</span>
                </div>
                <div className="p-2.5 rounded bg-[#151419] border border-[#37333D]/60">
                  <span className="text-[#A8A3AF] block text-[10px]">CATEGORY</span>
                  <span className="text-[#FB7185] font-bold">{selectedEvent.category || 'none'}</span>
                </div>
              </div>

              <div className="p-2.5 rounded bg-[#151419] border border-[#37333D]/60 text-[10px] text-[#A8A3AF] truncate">
                REQUEST ID: {selectedEvent.id}
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedEvent(null)}
                className="px-4 py-1.5 rounded-lg bg-[#242128] hover:bg-[#2A2730] text-xs font-mono text-[#F5F3F7] border border-[#37333D] transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
