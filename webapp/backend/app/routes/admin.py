from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta, timezone

from app.database import get_db
from app.models import User, UsageLog, Subscription, BinData, ActionType, UserTier, SubscriptionStatus
from app.utils.security import get_current_active_user

router = APIRouter()

# Pydantic models
class UserStatsResponse(BaseModel):
    total_users: int
    active_users: int
    premium_users: int
    free_users: int
    new_users_today: int
    new_users_this_month: int

class UsageStatsResponse(BaseModel):
    total_generations_today: int
    total_generations_this_month: int
    total_lookups_today: int
    total_lookups_this_month: int
    average_daily_usage: float

class RevenueStatsResponse(BaseModel):
    active_subscriptions: int
    monthly_recurring_revenue: float
    total_revenue_this_month: float
    churn_rate: float

class TopUserResponse(BaseModel):
    user_id: int
    email: str
    tier: UserTier
    total_generations: int
    total_lookups: int

class AdminDashboardResponse(BaseModel):
    user_stats: UserStatsResponse
    usage_stats: UsageStatsResponse
    revenue_stats: RevenueStatsResponse
    top_users: List[TopUserResponse]

def check_admin_access(current_user: User):
    """
    Check if user has admin access.
    For now, we'll use a simple email check.
    In production, you'd want a proper role system.
    """
    admin_emails = ["admin@yourdomain.com", "arturovillanueva1994@gmail.com"]  # Update with your admin emails
    if current_user.email not in admin_emails:
        raise HTTPException(status_code=403, detail="Admin access required")

@router.get("/dashboard", response_model=AdminDashboardResponse)
async def get_admin_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive admin dashboard data.
    """
    check_admin_access(current_user)
    
    # Date calculations
    today = datetime.utcnow().date()
    start_of_today = datetime.combine(today, datetime.min.time())
    start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month = (start_of_month - timedelta(days=1)).replace(day=1)
    
    # User Statistics
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    premium_users = db.query(User).filter(User.tier == UserTier.PREMIUM).count()
    free_users = db.query(User).filter(User.tier == UserTier.FREE).count()
    
    new_users_today = db.query(User).filter(User.created_at >= start_of_today).count()
    new_users_this_month = db.query(User).filter(User.created_at >= start_of_month).count()
    
    user_stats = UserStatsResponse(
        total_users=total_users,
        active_users=active_users,
        premium_users=premium_users,
        free_users=free_users,
        new_users_today=new_users_today,
        new_users_this_month=new_users_this_month
    )
    
    # Usage Statistics
    total_generations_today = db.query(UsageLog).filter(
        UsageLog.action == ActionType.CARD_GENERATION,
        UsageLog.created_at >= start_of_today
    ).count()
    
    total_generations_this_month = db.query(UsageLog).filter(
        UsageLog.action == ActionType.CARD_GENERATION,
        UsageLog.created_at >= start_of_month
    ).count()
    
    total_lookups_today = db.query(UsageLog).filter(
        UsageLog.action == ActionType.BIN_LOOKUP,
        UsageLog.created_at >= start_of_today
    ).count()
    
    total_lookups_this_month = db.query(UsageLog).filter(
        UsageLog.action == ActionType.BIN_LOOKUP,
        UsageLog.created_at >= start_of_month
    ).count()
    
    # Calculate average daily usage (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    daily_usage = db.query(func.count(UsageLog.id)).filter(
        UsageLog.created_at >= thirty_days_ago
    ).scalar()
    average_daily_usage = daily_usage / 30 if daily_usage else 0
    
    usage_stats = UsageStatsResponse(
        total_generations_today=total_generations_today,
        total_generations_this_month=total_generations_this_month,
        total_lookups_today=total_lookups_today,
        total_lookups_this_month=total_lookups_this_month,
        average_daily_usage=average_daily_usage
    )
    
    # Revenue Statistics
    active_subscriptions = db.query(Subscription).filter(
        Subscription.status == SubscriptionStatus.ACTIVE
    ).count()
    
    monthly_recurring_revenue = active_subscriptions * 9.99  # $9.99 per subscription
    
    # This month's revenue (simplified - in reality you'd sum actual payments)
    total_revenue_this_month = db.query(Subscription).filter(
        Subscription.created_at >= start_of_month,
        Subscription.status == SubscriptionStatus.ACTIVE
    ).count() * 9.99
    
    # Churn rate (simplified calculation)
    canceled_this_month = db.query(Subscription).filter(
        Subscription.status == SubscriptionStatus.CANCELED,
        Subscription.end_date >= start_of_month
    ).count()
    
    churn_rate = (canceled_this_month / max(active_subscriptions, 1)) * 100
    
    revenue_stats = RevenueStatsResponse(
        active_subscriptions=active_subscriptions,
        monthly_recurring_revenue=monthly_recurring_revenue,
        total_revenue_this_month=total_revenue_this_month,
        churn_rate=churn_rate
    )
    
    # Top Users
    top_users_query = db.query(
        User.id,
        User.email,
        User.tier,
        func.count(UsageLog.id).label('total_usage')
    ).join(UsageLog).group_by(User.id).order_by(desc('total_usage')).limit(10)
    
    top_users = []
    for user_id, email, tier, total_usage in top_users_query:
        generations = db.query(UsageLog).filter(
            UsageLog.user_id == user_id,
            UsageLog.action == ActionType.CARD_GENERATION
        ).count()
        
        lookups = db.query(UsageLog).filter(
            UsageLog.user_id == user_id,
            UsageLog.action == ActionType.BIN_LOOKUP
        ).count()
        
        top_users.append(TopUserResponse(
            user_id=user_id,
            email=email,
            tier=tier,
            total_generations=generations,
            total_lookups=lookups
        ))
    
    return AdminDashboardResponse(
        user_stats=user_stats,
        usage_stats=usage_stats,
        revenue_stats=revenue_stats,
        top_users=top_users
    )

@router.get("/users")
async def get_users(
    page: int = 1,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of users.
    """
    check_admin_access(current_user)
    
    offset = (page - 1) * limit
    users = db.query(User).offset(offset).limit(limit).all()
    total_users = db.query(User).count()
    
    return {
        "users": users,
        "total": total_users,
        "page": page,
        "limit": limit,
        "pages": (total_users + limit - 1) // limit
    }

@router.get("/usage-logs")
async def get_usage_logs(
    page: int = 1,
    limit: int = 100,
    action: Optional[ActionType] = None,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated usage logs with filters.
    """
    check_admin_access(current_user)
    
    query = db.query(UsageLog)
    
    if action:
        query = query.filter(UsageLog.action == action)
    if user_id:
        query = query.filter(UsageLog.user_id == user_id)
    
    total_logs = query.count()
    
    offset = (page - 1) * limit
    logs = query.order_by(desc(UsageLog.created_at)).offset(offset).limit(limit).all()
    
    return {
        "logs": logs,
        "total": total_logs,
        "page": page,
        "limit": limit,
        "pages": (total_logs + limit - 1) // limit
    }

@router.post("/users/{user_id}/upgrade")
async def upgrade_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Manually upgrade user to premium (admin override).
    """
    check_admin_access(current_user)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.tier = UserTier.PREMIUM
    db.commit()
    
    return {"message": f"User {user.email} upgraded to premium"}

@router.post("/users/{user_id}/downgrade")
async def downgrade_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Manually downgrade user to free tier (admin override).
    """
    check_admin_access(current_user)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.tier = UserTier.FREE
    db.commit()
    
    return {"message": f"User {user.email} downgraded to free tier"}

@router.get("/system-stats")
async def get_system_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get system-wide statistics.
    """
    check_admin_access(current_user)
    
    bin_count = db.query(BinData).count()
    total_usage = db.query(UsageLog).count()
    
    # Usage by action type
    usage_by_action = db.query(
        UsageLog.action,
        func.count(UsageLog.id).label('count')
    ).group_by(UsageLog.action).all()
    
    # Daily usage for last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    daily_usage_data = db.query(
        func.date(UsageLog.created_at).label('date'),
        func.count(UsageLog.id).label('count')
    ).filter(
        UsageLog.created_at >= thirty_days_ago
    ).group_by(func.date(UsageLog.created_at)).all()
    
    return {
        "bin_database_size": bin_count,
        "total_api_calls": total_usage,
        "usage_by_action": {action.value: count for action, count in usage_by_action},
        "daily_usage_last_30_days": [
            {"date": str(date), "count": count} 
            for date, count in daily_usage_data
        ]
    }
