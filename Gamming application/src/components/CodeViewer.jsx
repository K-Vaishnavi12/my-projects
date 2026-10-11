import { useState } from 'react'
import { Copy, Check } from 'lucide-react'
import './CodeViewer.css'

export default function CodeViewer({ code, language = 'python' }) {
    const [copied, setCopied] = useState(false)

    function handleCopy() {
        navigator.clipboard.writeText(code)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    // Simple syntax highlighting for Python
    function highlight(code) {
        const keywords = ['def', 'class', 'return', 'if', 'elif', 'else', 'for', 'while',
            'in', 'not', 'and', 'or', 'import', 'from', 'True', 'False', 'None',
            'print', 'len', 'range', 'self', 'pass', 'break', 'continue', 'lambda']
        let html = code
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/(#[^\n]*)/g, '<span class="cm-comment">$1</span>')
            .replace(/("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')/g, '<span class="cm-string">$1</span>')
            .replace(/\b(\d+)\b/g, '<span class="cm-number">$1</span>')
        keywords.forEach(kw => {
            html = html.replace(new RegExp(`\\b(${kw})\\b`, 'g'), '<span class="cm-keyword">$1</span>')
        })
        html = html.replace(/\b([a-zA-Z_]\w*)\s*(?=\()/g, '<span class="cm-func">$1</span>')
        return html
    }

    const lines = code.trim().split('\n')

    return (
        <div className="code-viewer">
            <div className="code-viewer-header">
                <div className="code-dots">
                    <div className="code-dot dot-red" />
                    <div className="code-dot dot-yellow" />
                    <div className="code-dot dot-green" />
                </div>
                <span className="code-lang">{language}</span>
                <button className="copy-btn" onClick={handleCopy}>
                    {copied ? <><Check size={14} /> Copied!</> : <><Copy size={14} /> Copy</>}
                </button>
            </div>
            <div className="code-body">
                <table className="code-table">
                    <tbody>
                        {lines.map((line, i) => (
                            <tr key={i} className="code-row">
                                <td className="line-num">{i + 1}</td>
                                <td
                                    className="line-code"
                                    dangerouslySetInnerHTML={{ __html: highlight(line) || '&nbsp;' }}
                                />
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}
