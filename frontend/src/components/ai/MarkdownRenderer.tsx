import React from 'react';
import ReactMarkdown from 'react-markdown';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  content,
  className = '',
}) => {
  return (
    <div className={`text-xs leading-relaxed ${className}`}>
      <ReactMarkdown
        components={{
          p: ({ children }) => (
            <p className="mb-2 last:mb-0 leading-relaxed text-slate-800 dark:text-slate-200">
              {children}
            </p>
          ),
          strong: ({ children }) => (
            <strong className="font-semibold text-slate-950 dark:text-white">
              {children}
            </strong>
          ),
          em: ({ children }) => (
            <em className="italic text-slate-700 dark:text-slate-300">
              {children}
            </em>
          ),
          h1: ({ children }) => (
            <h1 className="text-sm font-bold text-slate-950 dark:text-white mt-3 mb-1.5 first:mt-0">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-xs font-bold text-slate-950 dark:text-white mt-2.5 mb-1 first:mt-0">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-xs font-semibold text-slate-900 dark:text-slate-100 mt-2 mb-1 first:mt-0">
              {children}
            </h3>
          ),
          ul: ({ children }) => (
            <ul className="list-disc pl-4 mb-2 space-y-1 text-slate-800 dark:text-slate-200">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal pl-4 mb-2 space-y-1 text-slate-800 dark:text-slate-200">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="leading-relaxed">
              {children}
            </li>
          ),
          blockquote: ({ children }) => (
            <blockquote className="border-l-2 border-orange-500 pl-3 py-1 my-2 bg-slate-50 dark:bg-slate-800/40 text-slate-600 dark:text-slate-400 italic rounded-r">
              {children}
            </blockquote>
          ),
          code: ({ className: codeClassName, children, ...props }) => {
            const isInline = !codeClassName;
            if (isInline) {
              return (
                <code
                  className="font-mono text-[11px] px-1.5 py-0.5 rounded bg-slate-200/80 dark:bg-slate-800 text-orange-600 dark:text-orange-400 font-medium"
                  {...props}
                >
                  {children}
                </code>
              );
            }
            return (
              <code className={codeClassName} {...props}>
                {children}
              </code>
            );
          },
          pre: ({ children }) => (
            <pre className="p-3 my-2 rounded-lg bg-slate-950 text-slate-100 font-mono text-[11px] overflow-x-auto border border-slate-800 leading-relaxed">
              {children}
            </pre>
          ),
          hr: () => (
            <hr className="my-2.5 border-t border-slate-200 dark:border-slate-700" />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

