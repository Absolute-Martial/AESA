'use client';

import React, { useState } from 'react';
import { 
  GoalTracker, 
  DashboardHeader, 
  DashboardLayout,
} from '@/components/dashboard';
import { Button, Icon, Card } from '@/components/common';
import type { Goal } from '@/lib/types';

// Mock data for demonstration
const mockGoals: Goal[] = [
  {
    id: 'g1',
    title: 'Complete 20 hours of ML study',
    description: 'Focus on neural networks and deep learning',
    targetValue: 20,
    currentValue: 12,
    unit: 'hours',
    deadline: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
    status: 'active',
  },
  {
    id: 'g2',
    title: 'Finish 50 practice problems',
    description: 'Calculus and Linear Algebra problems',
    targetValue: 50,
    currentValue: 35,
    unit: 'problems',
    deadline: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000),
    status: 'active',
  },
  {
    id: 'g3',
    title: 'Read 5 chapters of Data Structures',
    targetValue: 5,
    currentValue: 3,
    unit: 'chapters',
    status: 'active',
  },
  {
    id: 'g4',
    title: 'Complete Physics Lab Reports',
    targetValue: 4,
    currentValue: 4,
    unit: 'reports',
    status: 'completed',
  },
];

const navItems = [
  { id: 'today', label: 'Today', icon: 'today', href: '/dashboard', isActive: false },
  { id: 'week', label: 'Week', icon: 'date_range', href: '/dashboard/week', isActive: false },
  { id: 'goals', label: 'Goals', icon: 'flag', href: '/dashboard/goals', isActive: true },
  { id: 'analytics', label: 'Analytics', icon: 'analytics', href: '/dashboard/analytics', isActive: false },
];

/**
 * Goals Page - Study goals tracking
 * Requirements: 16.1
 */
export default function GoalsPage() {
  const [goals, setGoals] = useState(mockGoals);

  const handleNavClick = (id: string) => {
    console.log('Navigate to:', id);
    // Would use router.push
  };

  const handleCreateGoal = (newGoal: Omit<Goal, 'id' | 'currentValue' | 'status'>) => {
    const goal: Goal = {
      ...newGoal,
      id: `g${Date.now()}`,
      currentValue: 0,
      status: 'active',
    };
    setGoals([...goals, goal]);
  };

  const handleUpdateProgress = (goalId: string, progress: number) => {
    setGoals(goals.map((g) => {
      if (g.id === goalId) {
        const newGoal = { ...g, currentValue: progress };
        // Auto-complete if target reached
        if (g.targetValue && progress >= g.targetValue) {
          newGoal.status = 'completed';
        }
        return newGoal;
      }
      return g;
    }));
  };

  const handleDeleteGoal = (goalId: string) => {
    setGoals(goals.filter((g) => g.id !== goalId));
  };

  // Calculate summary stats
  const activeGoals = goals.filter((g) => g.status === 'active');
  const completedGoals = goals.filter((g) => g.status === 'completed');
  const avgProgress = activeGoals.length > 0
    ? activeGoals.reduce((sum, g) => {
        if (!g.targetValue) return sum;
        return sum + (g.currentValue / g.targetValue) * 100;
      }, 0) / activeGoals.length
    : 0;

  return (
    <DashboardLayout
      header={
        <DashboardHeader
          userName="Student"
          navItems={navItems}
          onNavClick={handleNavClick}
          actions={
            <>
              <Button variant="ghost" icon="notifications" size="sm" />
              <Button variant="ghost" icon="settings" size="sm" />
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                <Icon name="person" size={18} className="text-primary" />
              </div>
            </>
          }
        />
      }
    >
      <div className="p-6 max-w-4xl mx-auto">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-display font-bold text-text-main mb-2">
            Study Goals
          </h1>
          <p className="text-text-muted">
            Track your progress and stay motivated
          </p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          <Card variant="elevated" padding="md">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <Icon name="flag" size={20} className="text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold text-text-main">{activeGoals.length}</p>
                <p className="text-xs text-text-muted">Active Goals</p>
              </div>
            </div>
          </Card>
          <Card variant="elevated" padding="md">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <Icon name="check_circle" size={20} className="text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-text-main">{completedGoals.length}</p>
                <p className="text-xs text-text-muted">Completed</p>
              </div>
            </div>
          </Card>
          <Card variant="elevated" padding="md">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Icon name="trending_up" size={20} className="text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-text-main">{Math.round(avgProgress)}%</p>
                <p className="text-xs text-text-muted">Avg Progress</p>
              </div>
            </div>
          </Card>
        </div>

        {/* Goal Tracker */}
        <Card variant="elevated" padding="lg">
          <GoalTracker
            goals={goals}
            onCreateGoal={handleCreateGoal}
            onUpdateProgress={handleUpdateProgress}
            onDeleteGoal={handleDeleteGoal}
          />
        </Card>
      </div>
    </DashboardLayout>
  );
}
