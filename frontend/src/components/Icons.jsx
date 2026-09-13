import React from 'react'

/*
 * Thin geometric line marks (1.5px stroke) - no icon library. Kept intentionally
 * spare so the amber accent, not iconography, carries visual weight.
 */
const base = {
  width: 16,
  height: 16,
  viewBox: '0 0 16 16',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.5,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
  'aria-hidden': true,
}

export const SendIcon = (props) => (
  <svg {...base} {...props}>
    <path d="M1.5 8 14.5 1.5 9.5 14.5 7 9l-5.5-1Z" />
  </svg>
)

export const PlusIcon = (props) => (
  <svg {...base} {...props}>
    <path d="M8 2v12M2 8h12" />
  </svg>
)

export const TrashIcon = (props) => (
  <svg {...base} {...props}>
    <path d="M3 4.5h10M6.5 4.5V3a1 1 0 0 1 1-1h1a1 1 0 0 1 1 1v1.5M4.5 4.5l.6 8.4a1 1 0 0 0 1 .9h3.8a1 1 0 0 0 1-.9l.6-8.4" />
  </svg>
)

export const CopyIcon = (props) => (
  <svg {...base} {...props}>
    <rect x="5.5" y="5.5" width="8" height="8" rx="1" />
    <path d="M2.5 10.5V3a1 1 0 0 1 1-1H10" />
  </svg>
)

export const DownloadIcon = (props) => (
  <svg {...base} {...props}>
    <path d="M8 2v8m0 0 3-3m-3 3-3-3M2.5 12.5h11" />
  </svg>
)

export const RegenIcon = (props) => (
  <svg {...base} {...props}>
    <path d="M2.5 8a5.5 5.5 0 0 1 9.3-4M13.5 8a5.5 5.5 0 0 1-9.3 4M11 3.2v2.6h-2.6M5 12.8v-2.6h2.6" />
  </svg>
)

export const CheckIcon = (props) => (
  <svg {...base} {...props}>
    <path d="M2.5 8.5 6 12l7.5-8" />
  </svg>
)

export const AlertIcon = (props) => (
  <svg {...base} {...props}>
    <path d="M8 1.5 14.75 13.5H1.25L8 1.5Z" />
    <path d="M8 6.3v3.4" strokeLinecap="round" />
    <circle cx="8" cy="11.8" r="0.15" fill="currentColor" stroke="none" />
  </svg>
)
