import React from 'react';
import { X, Copy, Check, FileCode, ArrowLeft } from 'lucide-react';

interface ReportModalProps {
  title: string;
  data: unknown;
  isOpen: boolean;
  onClose: () => void;
}

export const ReportModal: React.FC<ReportModalProps> = ({
  title,
  data,
  isOpen,
  onClose,
}) => {
  const [copied, setCopied] = React.useState(false);

  if (!isOpen) return null;

  const jsonString = JSON.stringify(data, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(jsonString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
      <div className="bg-[#121720] border border-[#26303d] rounded-xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-[#26303d] flex items-center justify-between bg-[#0e131b]">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[#17202c] rounded-lg border border-[#26303d] text-[#66e3c4]">
              <FileCode className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xs font-mono text-[#8d9aaa] uppercase tracking-wider">
                Veklom Canonical Evidence & Report
              </span>
              <h2 className="text-lg font-bold text-[#eef3f8]">{title}</h2>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-[#1a222f] hover:bg-[#222d3d] text-[#eef3f8] border border-[#26303d] flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-[#66e3c4]" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied' : 'Copy JSON'}</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-[#8d9aaa] hover:text-[#eef3f8] hover:bg-[#1a222f] transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Content */}
        <div className="p-6 overflow-y-auto font-mono text-xs leading-relaxed text-[#c8f6e9] bg-[#0b0e13]">
          <pre className="whitespace-pre-wrap break-all select-text font-mono">
            {jsonString}
          </pre>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 border-t border-[#26303d] bg-[#0e131b] flex items-center justify-between text-xs text-[#8d9aaa]">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[#66e3c4]"></span>
            GnomLedger / PGL verified evidence format
          </span>
          <button
            onClick={onClose}
            className="text-[#66e3c4] hover:underline flex items-center gap-1 cursor-pointer font-medium"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Close report viewer
          </button>
        </div>
      </div>
    </div>
  );
};
