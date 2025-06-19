from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.db import get_async_db
from backend.models.group import Group
from backend.models.GroupMember import GroupMember
from backend.models.user import User
from backend.schemas.GroupMember import GroupMemberRead, GroupMemberUpdate
from backend.schemas.group import GroupCreate, GroupRead

router = APIRouter(prefix="/groups", tags=["Groups"])


@router.post("/", response_model=GroupRead)
async def create_group(
    data: GroupCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    group = Group(name=data.name, creator_id=current_user.id)
    db.add(group)
    await db.commit()
    await db.refresh(group)

    member = GroupMember(group_id=group.id, user_id=current_user.id, status="joined")
    db.add(member)
    await db.commit()
    await db.refresh(member)

    return group


@router.get("/", response_model=List[GroupRead])
async def get_my_groups(db: AsyncSession = Depends(get_async_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Group, User.username)
        .join(User, Group.creator_id == User.id)
        .join(GroupMember, Group.id == GroupMember.group_id)
        .where(GroupMember.user_id == current_user.id, GroupMember.status == "joined")
    )
    groups = result.all()
    return [
        {
            "id": g.Group.id,
            "name": g.Group.name,
            "creator_id": g.Group.creator_id,
            "creator_username": g.username,
        }
        for g in groups
    ]

@router.post("/{group_id}/invite", response_model=GroupMemberRead)
async def invite_user(
    group_id: int,
    data: GroupMemberUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Grupul nu există")
    if group.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Doar creatorul grupului poate invita membri")

    result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == data.user_id
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Utilizatorul este deja în grup sau a fost invitat")

    member = GroupMember(group_id=group_id, user_id=data.user_id, status="invited")
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


@router.post("/{group_id}/accept", response_model=GroupMemberRead)
async def accept_invite(
    group_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == current_user.id
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Invitație inexistentă")
    if member.status != "invited":
        raise HTTPException(status_code=400, detail="Nu poți accepta această invitație")

    member.status = "joined"
    await db.commit()
    await db.refresh(member)
    return member


@router.get("/{group_id}/members")
async def get_group_members(group_id: int, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(
        select(GroupMember.id, GroupMember.status, User.username)
        .join(User, GroupMember.user_id == User.id)
        .where(GroupMember.group_id == group_id)
    )
    members = result.all()
    return [
        {"id": m.id, "status": m.status, "username": m.username}
        for m in members
    ]



@router.delete("/{group_id}")
async def delete_group(
    group_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Grupul nu există")
    if group.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Doar creatorul grupului îl poate șterge")

    await db.delete(group)
    await db.commit()
    return {"message": "Grupul a fost șters"}

@router.get("/invitations", response_model=List[GroupRead])
async def get_invitations(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Group, User.username)
        .join(User, Group.creator_id == User.id)
        .join(GroupMember, Group.id == GroupMember.group_id)
        .where(GroupMember.user_id == current_user.id)
        .where(GroupMember.status == "invited")
    )
    rows = result.all()

    return [
        {
            "id": group.id,
            "name": group.name,
            "creator_id": group.creator_id,
            "creator_username": username
        }
        for group, username in rows
    ]


@router.post("/{group_id}/request")
async def request_to_join(
    group_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Group).filter_by(id=group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Grupul nu există")

    existing = await db.execute(
        select(GroupMember).filter_by(group_id=group_id, user_id=current_user.id)
    )
    if existing.scalar():
        raise HTTPException(status_code=400, detail="Ești deja în grup sau invitat")

    new_member = GroupMember(
        group_id=group_id,
        user_id=current_user.id,
        status="invited"
    )
    db.add(new_member)
    await db.commit()
    return {"message": "Cererea a fost trimisă"}


@router.get("/all", response_model=List[GroupRead])
async def get_all_groups(db: AsyncSession = Depends(get_async_db)):
    stmt = select(Group, User.username).join(User, Group.creator_id == User.id)
    result = await db.execute(stmt)
    groups = result.all()

    return [
        {
            "id": g.id,
            "name": g.name,
            "creator_id": g.creator_id,
            "creator_username": username
        }
        for g, username in groups
    ]

@router.get("/requests")
async def get_group_join_requests(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Group.id).where(Group.creator_id == current_user.id))
    owned_groups = result.scalars().all()

    if not owned_groups:
        return []

    result = await db.execute(
        select(
            GroupMember.id,
            GroupMember.group_id,
            GroupMember.user_id,
            GroupMember.status,
            GroupMember.joined_at,
            Group.name.label("group_name"),
            User.username
        )
        .join(Group, GroupMember.group_id == Group.id)
        .join(User, GroupMember.user_id == User.id)
        .where(Group.creator_id == current_user.id)
        .where(GroupMember.status == "invited")
    )

    rows = result.all()
    return [
        {
            "id": r.id,
            "group_id": r.group_id,
            "user_id": r.user_id,
            "status": r.status,
            "joined_at": r.joined_at,
            "group_name": r.group_name,
            "username": r.username,
        }
        for r in rows
    ]


@router.post("/{group_id}/requests/{user_id}/accept")
async def accept_join_request(
    group_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    group = await db.scalar(select(Group).where(Group.id == group_id))
    if not group or group.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Nu ai dreptul să accepți cereri pentru acest grup")

    member = await db.scalar(select(GroupMember).where(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id,
        GroupMember.status == "invited"
    ))

    if not member:
        raise HTTPException(status_code=404, detail="Cererea nu există")

    member.status = "joined"
    await db.commit()
    return {"message": "Cererea a fost acceptată"}

@router.post("/{group_id}/requests/{user_id}/reject")
async def reject_join_request(
    group_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    group = await db.scalar(select(Group).where(Group.id == group_id))
    if not group or group.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Nu ai dreptul să respingi cereri pentru acest grup")

    member = await db.scalar(select(GroupMember).where(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id,
        GroupMember.status == "invited"
    ))

    if not member:
        raise HTTPException(status_code=404, detail="Cererea nu există")

    await db.delete(member)
    await db.commit()
    return {"message": "Cererea a fost respinsă"}


