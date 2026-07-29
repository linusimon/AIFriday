import { Component, OnInit } from '@angular/core';
import { TaskRoutingService } from '../services/task-routing.service';
import { ProjectExecutionPlan, UserStory, SprintMilestone } from '../models/task-routing.model';

@Component({
  selector: 'app-execution-plans',
  templateUrl: './execution-plans.component.html',
  styleUrls: ['./execution-plans.component.css']
})
export class ExecutionPlansComponent implements OnInit {
  plans: ProjectExecutionPlan[] = [];
  selectedPlan: ProjectExecutionPlan | null = null;
  activeModalTab: 'stories' | 'timeline' | 'team' = 'stories';
  
  loading: boolean = false;
  generating: boolean = false;
  error: string | null = null;
  successMsg: string | null = null;

  // Search & Filter
  searchQuery: string = '';
  selectedSprintFilter: string = 'all';

  latestPlan: ProjectExecutionPlan | null = null;
  latestActiveTab: 'stories' | 'timeline' | 'team' = 'stories';
  latestSprintFilter: string = 'all';
  latestSearchQuery: string = '';

  constructor(private taskRoutingService: TaskRoutingService) {}

  ngOnInit(): void {
    this.loadPlans();
  }

  loadPlans(): void {
    this.loading = true;
    this.error = null;
    this.taskRoutingService.getExecutionPlans().subscribe({
      next: (res: any) => {
        const rawPlans: ProjectExecutionPlan[] = res.plans || [];
        this.plans = rawPlans.sort((a, b) => (b.plan_id || 0) - (a.plan_id || 0));
        this.latestPlan = this.plans.length > 0 ? this.plans[0] : null;
        this.loading = false;
      },
      error: (err: any) => {
        this.error = 'Failed to load project execution plans.';
        this.loading = false;
        console.error('Execution plans load error:', err);
      }
    });
  }

  openPlanModal(plan: ProjectExecutionPlan): void {
    this.selectedPlan = plan;
    this.activeModalTab = 'stories';
  }

  closePlanModal(): void {
    this.selectedPlan = null;
  }

  deletePlan(planId: number, event: Event): void {
    event.stopPropagation();
    if (!confirm('Are you sure you want to delete this project execution plan?')) {
      return;
    }

    this.taskRoutingService.deleteExecutionPlan(planId).subscribe({
      next: () => {
        this.plans = this.plans.filter(p => p.plan_id !== planId);
        if (this.selectedPlan?.plan_id === planId) {
          this.selectedPlan = null;
        }
        if (this.latestPlan?.plan_id === planId) {
          this.latestPlan = this.plans.length > 0 ? this.plans[0] : null;
        }
        this.successMsg = 'Execution plan deleted successfully.';
        setTimeout(() => this.successMsg = null, 4000);
      },
      error: (err: any) => {
        this.error = 'Failed to delete execution plan.';
        console.error(err);
      }
    });
  }

  get latestFilteredUserStories(): UserStory[] {
    if (!this.latestPlan || !this.latestPlan.user_stories) return [];
    let stories = this.latestPlan.user_stories;

    if (this.latestSprintFilter !== 'all') {
      stories = stories.filter(s => s.sprint === this.latestSprintFilter);
    }

    if (this.latestSearchQuery.trim()) {
      const q = this.latestSearchQuery.toLowerCase();
      stories = stories.filter(s => 
        s.story_id.toLowerCase().includes(q) ||
        s.title.toLowerCase().includes(q) ||
        s.assigned_to.toLowerCase().includes(q)
      );
    }

    return stories;
  }

  get filteredUserStories(): UserStory[] {
    if (!this.selectedPlan || !this.selectedPlan.user_stories) return [];
    let stories = this.selectedPlan.user_stories;

    if (this.selectedSprintFilter !== 'all') {
      stories = stories.filter(s => s.sprint === this.selectedSprintFilter);
    }

    if (this.searchQuery.trim()) {
      const q = this.searchQuery.toLowerCase();
      stories = stories.filter(s => 
        s.story_id.toLowerCase().includes(q) ||
        s.title.toLowerCase().includes(q) ||
        s.assigned_to.toLowerCase().includes(q)
      );
    }

    return stories;
  }

  get totalKpiUserStories(): number {
    return this.plans.reduce((acc, p) => acc + (p.total_user_stories || 0), 0);
  }

  get totalKpiHours(): number {
    return this.plans.reduce((acc, p) => acc + (p.total_effort_hours || 0), 0);
  }

  get totalKpiCost(): number {
    return this.plans.reduce((acc, p) => acc + (p.total_cost || 0), 0);
  }

  exportPlanAsMarkdown(plan: ProjectExecutionPlan, event: Event): void {
    event.stopPropagation();
    let md = `# ${plan.plan_name}\n\n`;
    md += `**Description**: ${plan.description}\n\n`;
    md += `**Source**: ${plan.source}\n`;
    md += `**Total User Stories**: ${plan.total_user_stories} | **Total Points**: ${plan.total_story_points} | **Effort**: ${plan.total_effort_hours} hrs | **Cost**: $${plan.total_cost}\n\n`;

    md += `## Agile User Stories\n\n`;
    md += `| ID | Title | Priority | Assigned To | Points | Hours | Cost | Sprint |\n`;
    md += `|---|---|---|---|---|---|---|---|\n`;
    (plan.user_stories || []).forEach(s => {
      md += `| ${s.story_id} | ${s.title} | ${s.priority} | ${s.assigned_to} (${s.assigned_type}) | ${s.story_points} | ${s.estimated_effort_hours} | $${s.estimated_cost} | ${s.sprint} |\n`;
    });

    md += `\n## Sprint Roadmap Timeline\n\n`;
    (plan.timeline || []).forEach(tm => {
      md += `### ${tm.sprint_name} (${tm.start_date} to ${tm.end_date})\n`;
      md += `- **Deliverables**: ${tm.key_deliverables.join(', ')}\n`;
      md += `- **Stories**: ${tm.story_ids.join(', ')}\n\n`;
    });

    const blob = new Blob([md], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${plan.plan_name.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.md`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}
