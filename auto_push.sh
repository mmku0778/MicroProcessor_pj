#!/bin/bash

# ==========================================
# GitHub 자동 업로드 스크립트
# ==========================================

# 1. 변경된 모든 파일(추가, 수정, 삭제)을 장바구니(Staging Area)에 담기
# (.gitignore에 명시된 파일들은 자동으로 제외됩니다)
echo "📦 변경된 파일들을 장바구니에 담습니다..."
git add .

# 2. 커밋 메시지 작성
# 커밋 메시지를 입력받거나, 입력이 없으면 현재 시간을 기본 메시지로 사용
echo -n "✍️  커밋 메시지를 입력하세요 (엔터 치면 자동 시간 입력): "
read commit_message

if [ -z "$commit_message" ]; then
    commit_message="Auto commit: $(date +'%Y-%m-%d %H:%M:%S')"
fi

# 3. 사진 찍기 (버전 생성)
echo "📸 버전을 생성합니다..."
git commit -m "$commit_message"

# 4. GitHub로 밀어 올리기 (main 브랜치 기준)
echo "🚀 GitHub로 파일들을 업로드합니다..."
git push origin main

echo "✅ 업로드가 완료되었습니다!"
