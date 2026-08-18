/**
 * Skeleton Loading Components
 * Reusable components for loading states
 */

import { cn } from '@/lib/utils';

// ============================================================
// Base Skeleton
// ============================================================

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        'animate-pulse bg-slate-200 rounded',
        className
      )}
    />
  );
}

// ============================================================
// SkeletonText
// ============================================================

interface SkeletonTextProps {
  lines?: number;
  className?: string;
}

export function SkeletonText({ lines = 3, className }: SkeletonTextProps) {
  return (
    <div className={cn('space-y-2', className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          className={cn(
            'h-4',
            i === lines - 1 ? 'w-3/4' : 'w-full'
          )}
        />
      ))}
    </div>
  );
}

// ============================================================
// SkeletonCard
// ============================================================

interface SkeletonCardProps {
  className?: string;
}

export function SkeletonCard({ className }: SkeletonCardProps) {
  return (
    <div
      className={cn(
        'bg-white rounded-2xl shadow-lg border border-slate-100 p-6',
        className
      )}
    >
      <div className="space-y-4">
        <div className="flex items-center gap-4">
          <Skeleton className="w-12 h-12 rounded-xl" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-1/3" />
            <Skeleton className="h-3 w-1/2" />
          </div>
        </div>
        <SkeletonText lines={2} />
      </div>
    </div>
  );
}

// ============================================================
// SkeletonTable
// ============================================================

interface SkeletonTableProps {
  rows?: number;
  columns?: number;
}

export function SkeletonTable({ rows = 5, columns = 4 }: SkeletonTableProps) {
  return (
    <div className="bg-white rounded-2xl shadow-lg border border-slate-100 overflow-hidden">
      {/* Header */}
      <div className="bg-slate-50 px-6 py-4 border-b border-slate-100">
        <div className="flex gap-4">
          {Array.from({ length: columns }).map((_, i) => (
            <Skeleton key={i} className="h-4 flex-1" />
          ))}
        </div>
      </div>

      {/* Rows */}
      <div className="divide-y divide-slate-100">
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <div key={rowIndex} className="px-6 py-4">
            <div className="flex gap-4 items-center">
              {Array.from({ length: columns }).map((_, colIndex) => (
                <Skeleton
                  key={colIndex}
                  className={cn(
                    'h-4 flex-1',
                    colIndex === 0 && 'flex-[2]', // First column wider
                    colIndex === columns - 1 && 'flex-[0.5]' // Last column narrower
                  )}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================
// SkeletonStats
// ============================================================

interface SkeletonStatsProps {
  count?: number;
}

export function SkeletonStats({ count = 6 }: SkeletonStatsProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="bg-white rounded-2xl shadow-lg border border-slate-100 p-5"
        >
          <div className="flex items-center gap-3 mb-3">
            <Skeleton className="w-10 h-10 rounded-xl" />
          </div>
          <Skeleton className="h-8 w-2/3 mb-2" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      ))}
    </div>
  );
}

// ============================================================
// SkeletonPrediction
// ============================================================

export function SkeletonPrediction() {
  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fade-in">
      {/* Header */}
      <div className="text-center space-y-2">
        <Skeleton className="h-10 w-64 mx-auto" />
        <Skeleton className="h-5 w-96 mx-auto" />
      </div>

      {/* Input Card */}
      <div className="bg-white rounded-2xl shadow-lg border border-slate-100 p-8">
        <Skeleton className="h-4 w-32 mb-3" />
        <Skeleton className="h-32 w-full mb-4" />
        <div className="flex justify-between items-center">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-12 w-32 rounded-xl" />
        </div>
      </div>

      {/* Result Card Placeholder */}
      <div className="bg-white rounded-2xl shadow-lg border border-slate-100 p-8">
        <Skeleton className="h-24 w-full" />
      </div>
    </div>
  );
}

// ============================================================
// SkeletonHistory
// ============================================================

interface SkeletonHistoryProps {
  count?: number;
}

export function SkeletonHistory({ count = 5 }: SkeletonHistoryProps) {
  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="text-center space-y-2">
        <Skeleton className="h-10 w-48 mx-auto" />
        <Skeleton className="h-5 w-64 mx-auto" />
      </div>

      {/* Filter Card */}
      <div className="bg-white rounded-2xl shadow-lg border border-slate-100 p-4">
        <div className="flex gap-4 items-center">
          <Skeleton className="h-10 flex-1" />
          <Skeleton className="h-10 w-24" />
          <Skeleton className="h-10 w-24" />
          <Skeleton className="h-10 w-24" />
        </div>
      </div>

      {/* History Items */}
      <div className="space-y-4">
        {Array.from({ length: count }).map((_, i) => (
          <div
            key={i}
            className="bg-white rounded-2xl shadow-lg border border-slate-100 p-6"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 space-y-3">
                <div className="flex items-center gap-3">
                  <Skeleton className="h-6 w-24 rounded-full" />
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-5 w-16 rounded" />
                </div>
                <Skeleton className="h-5 w-full" />
                <div className="flex gap-4">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-4 w-16" />
                  <Skeleton className="h-4 w-20" />
                </div>
              </div>
              <Skeleton className="h-8 w-8 rounded" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================
// SkeletonBatch
// ============================================================

export function SkeletonBatch() {
  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-fade-in">
      {/* Header */}
      <div className="text-center space-y-2">
        <Skeleton className="h-10 w-48 mx-auto" />
        <Skeleton className="h-5 w-64 mx-auto" />
      </div>

      {/* Upload Card */}
      <div className="bg-white rounded-2xl shadow-lg border border-slate-100 p-8">
        <Skeleton className="h-48 w-full rounded-2xl mb-4" />
        <Skeleton className="h-4 w-full mb-2" />
        <Skeleton className="h-4 w-3/4 mb-6" />
        <div className="flex justify-end">
          <Skeleton className="h-12 w-32 rounded-xl" />
        </div>
      </div>
    </div>
  );
}

// ============================================================
// SkeletonAdmin
// ============================================================

export function SkeletonAdmin() {
  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <Skeleton className="h-10 w-48" />

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <SkeletonCard />
        <SkeletonCard />
      </div>

      {/* Users Table */}
      <SkeletonTable rows={5} columns={3} />

      {/* Activity Table */}
      <SkeletonTable rows={5} columns={4} />
    </div>
  );
}
