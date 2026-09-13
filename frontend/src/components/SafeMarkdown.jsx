import React from 'react'
import ReactMarkdown from 'react-markdown'

// react-markdown never uses dangerouslySetInnerHTML - it builds real DOM nodes,
// so restricting the component map is sufficient sanitization on its own. The
// allowed set mirrors the backend's HTML artifact whitelist (bleach in
// src/routers/artifacts.py) for a consistent security story across both
// rendering paths.
const ALLOWED = new Set([
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
  'p', 'ul', 'ol', 'li', 'strong', 'em', 'a', 'blockquote', 'code', 'pre', 'br',
])

const components = Object.fromEntries(
  [...ALLOWED].map((tag) => [
    tag,
    ({ node, ...props }) =>
      tag === 'a' ? (
        <a {...props} target="_blank" rel="noopener noreferrer" />
      ) : (
        React.createElement(tag, props)
      ),
  ])
)

export default function SafeMarkdown({ children, className }) {
  return (
    <div className={className}>
      <ReactMarkdown
        allowedElements={[...ALLOWED]}
        unwrapDisallowed
        components={components}
      >
        {children}
      </ReactMarkdown>
    </div>
  )
}
