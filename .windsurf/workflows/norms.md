---
description: Guidelines for Windsurf to follow implementation norms
---

# Implementation Norms for 7H Stock Analyzer

## Core Norms to Follow

### 1. Pre-Implementation Planning
**Always check implementation plan before implementing:**
- Verify cost implications are documented
- Confirm security considerations are addressed
- Review for any gaps in the current plan
- Use existing `@aws-deployment-plan.md` for all documentation

**Implementation Checklist:**
- [ ] Cost analysis complete and within budget
- [ ] Security review passed
- [ ] No gaps identified in deployment plan
- [ ] All dependencies accounted for

### 2. Documentation Management
**Markdown Files:**
- **NEVER** create new markdown files
- **ALWAYS** add content to existing `doc/aws-deployment-plan.md`
- Use `@aws-deployment-plan.md` reference for all documentation
- Update existing sections rather than creating new ones

**Content Organization:**
- Add new sections under appropriate existing headings
- Update status sections (✅ COMPLETED, ⏳ PENDING, ❌ MISSING)
- Maintain existing formatting and structure
- Use consistent markdown formatting

### 3. Configuration Management
**Configuration Files:**
- **NEVER** create additional configuration files
- **ALWAYS** modify existing configuration files
- Squeeze new configurations into existing files
- Maintain backward compatibility
- **KEEP AWS CONFIG FILES SYNCED** - latest changes must be reflected in existing configs
- **NO CONFIG FILE PROLIFERATION** - avoid multiple similar config files

**Existing Configuration Locations:**
- Environment variables: `.env.local`
- AWS configs: `infra/aws/template.yaml`
- Deployment configs: `infra/aws/deploy_aws_onetime.sh`
- Application configs: `backend/app/config.py`

**AWS Config Sync Requirements:**
- **ALWAYS** update existing AWS config files with latest changes
- **NEVER** create separate AWS config files for variations
- **CONSOLIDATE** all AWS configuration changes in existing templates
- **MAINTAIN** single source of truth for each AWS service config
- **SYNC** related AWS config files when changes are made

### 4. File Creation Policy
**Allowed:**
- Code files (Python, JavaScript, etc.)
- Test files
- Build/deployment scripts (if absolutely necessary)

**Prohibited:**
- New markdown documentation files
- Additional configuration files
- Duplicate functionality files

### 5. File Cleanup Policy
**Windsurf-Created Files Cleanup:**
- **ALWAYS** review Windsurf-created temporary files/scripts
- **DOUBLE-CHECK** if files are actually being used
- **REMOVE** unused Windsurf-created files immediately
- **MAINTAIN** clean workspace without redundant files

**Cleanup Process:**
1. Identify Windsurf-created temporary files and scripts
2. Verify if files are referenced or used in the codebase
3. Remove unused files to prevent workspace clutter
4. Document any important files that should be kept

**Common Files to Review:**
- Temporary scripts in `infra/local/`
- Test files that are no longer needed
- Backup or duplicate files
- Development artifacts and temporary outputs

### 6. Implementation Process
**Before Implementation:**
1. Review `doc/aws-deployment-plan.md` for current status
2. Check cost implications in existing documentation
3. Verify security measures are documented
4. Identify gaps in current implementation

**During Implementation:**
1. Update `aws-deployment-plan.md` with progress
2. Modify existing config files only
3. Add code to existing files when possible
4. Document any deviations from plan

**After Implementation:**
1. Update completion status in `aws-deployment-plan.md`
2. Verify cost estimates are still accurate
3. Confirm security measures are implemented
4. Test all modifications work correctly

### 7. Cost & Security Validation
**Cost Checks:**
- Verify monthly cost estimates in documentation
- Check for additional service costs
- Ensure free tier usage is optimized
- Update cost breakdown if changes made

**Security Checks:**
- Review IAM permissions in templates
- Verify API key handling
- Check S3 bucket policies
- Confirm encryption settings
- Validate network security configurations
- **Security vulnerability assessment for all AWS capabilities**
- **Review new AWS services for security implications**
- **Check for exposed credentials or sensitive data**
- **Validate least privilege principle implementation**

### 8. Documentation Updates Required
**For Each Implementation:**
- Update "Current Status & Next Steps" section
- Modify "Gap Analysis & Resolution Strategy" if applicable
- Update "Cost Impact Analysis" with any changes
- Refresh "Security Configuration" if security changes made
- Update "Success Criteria" checklist

### 9. Quality Assurance
**Before Finalizing:**
- All configurations in existing files
- Documentation updated in `aws-deployment-plan.md`
- No new markdown files created
- No new configuration files created
- Cost and security implications documented

## Enforcement Commands

### Check Compliance
```bash
# Verify no new markdown files were created
find . -name "*.md" -newer doc/aws-deployment-plan.md | grep -v "aws-deployment-plan.md"

# Verify no new config files were created
find . -name "*.config" -o -name "*.yaml" -o -name "*.yml" -o -name ".env*" | grep -v "node_modules"

# Check AWS config files are synced
echo "🔄 Checking AWS config sync status..."
AWS_CONFIGS=("infra/aws/template.yaml" "infra/aws/template-minimal.yaml" "infra/aws/template-lambda-only.yaml")
for config in "${AWS_CONFIGS[@]}"; do
    if [[ -f "$config" ]]; then
        echo "✅ Found: $config"
    else
        echo "⚠️  Missing: $config"
    fi
done

# Check for unused Windsurf-created files
echo "🔍 Checking for unused Windsurf-created files..."
find . -name "*.tmp" -o -name "*~" -o -name "*.bak" -o -name "*.orig" | grep -v node_modules

# Security vulnerability assessment for AWS capabilities
echo "🔒 Running security vulnerability assessment..."
```

### Update Documentation
```bash
# Always update the main deployment plan
echo "Implementation completed - update doc/aws-deployment-plan.md"
```

## Examples of Correct Implementation

### ✅ Correct: Adding New Feature
1. Update `doc/aws-deployment-plan.md` with new section
2. Modify `backend/app/config.py` for new config
3. Add code to existing `backend/app/api/` files
4. Update status in deployment plan

### ❌ Incorrect: Adding New Feature
1. Create `doc/new-feature.md` (PROHIBITED)
2. Create `backend/config/new-config.yaml` (PROHIBITED)
3. Create separate documentation files (PROHIBITED)

## Active Enforcement During Development

### Pre-Implementation Checklist (Mandatory)
Before any code implementation, Windsurf must:

1. **Check Cost/Security Gaps**
   ```bash
   # Review current status in deployment plan
   grep -A 5 -B 5 "Gap Analysis" doc/aws-deployment-plan.md
   grep -A 10 "Cost Impact" doc/aws-deployment-plan.md
   ```

2. **Verify Documentation Location**
   - Confirm content belongs in `doc/aws-deployment-plan.md`
   - Identify existing section to update
   - Plan content integration approach

3. **Check Configuration Consolidation**
   - Identify existing config file to modify
   - Verify no new config files needed
   - Plan configuration integration
   - **Ensure AWS config files remain synced**

### Real-Time Enforcement Checks

### During Implementation - Auto Checks
Windsurf should automatically run these checks during implementation:

```bash
# 1. Prevent new markdown file creation
if [[ $(find . -name "*.md" -newer doc/aws-deployment-plan.md | grep -v "aws-deployment-plan.md" | wc -l) -gt 0 ]]; then
    echo "❌ VIOLATION: New markdown files detected. Use doc/aws-deployment-plan.md instead."
    exit 1
fi

# 2. Prevent new config file creation  
if [[ $(find . -name "*.config" -o -name "*.yaml" -o -name "*.yml" -o -name ".env*" | grep -v "node_modules" | grep -v "template.yaml" | wc -l) -gt $(git ls-files "*.config" "*.yaml" "*.yml" ".env*" | wc -l) ]]; then
    echo "❌ VIOLATION: New configuration files detected. Modify existing files only."
    exit 1
fi

# 3. Verify deployment plan updated
if [[ $(git diff --name-only | grep "doc/aws-deployment-plan.md" | wc -l) -eq 0 ]]; then
    echo "⚠️  WARNING: Deployment plan not updated. Please update doc/aws-deployment-plan.md"
fi

# 4. Check for unused Windsurf-created files
echo "🔍 Checking for unused Windsurf-created files..."
TEMP_FILES=$(find . -name "*.tmp" -o -name "*~" -o -name "*.bak" -o -name "*.orig" | grep -v node_modules)
if [[ ! -z "$TEMP_FILES" ]]; then
    echo "⚠️  WARNING: Temporary files found. Review and remove if unused:"
    echo "$TEMP_FILES"
fi

# 6. AWS config sync validation
echo "🔄 Checking AWS config sync status..."
AWS_CONFIGS=("infra/aws/template.yaml" "infra/aws/template-minimal.yaml" "infra/aws/template-lambda-only.yaml")
SYNC_ISSUES=0
for config in "${AWS_CONFIGS[@]}"; do
    if [[ -f "$config" ]]; then
        echo "✅ Found: $config"
        # Check if this config was modified in current changes
        if git diff --name-only | grep -q "$config"; then
            echo "🔄 $config was modified - checking if other AWS configs need sync..."
            # Alert user to check other AWS configs for consistency
            for other_config in "${AWS_CONFIGS[@]}"; do
                if [[ "$other_config" != "$config" && -f "$other_config" ]]; then
                    echo "⚠️  REMINDER: Review $other_config for sync with changes in $config"
                fi
            done
        fi
    else
        echo "⚠️  Missing: $config"
        SYNC_ISSUES=$((SYNC_ISSUES + 1))
    fi
done
if [[ $SYNC_ISSUES -gt 0 ]]; then
    echo "❌ AWS config sync issues detected. Please ensure all AWS config files are present and consistent."
fi
# 7. Security vulnerability assessment for AWS capabilities
echo "🔒 Running security vulnerability assessment..."
# Check for new AWS services introduced in changes
AWS_CHANGES=$(git diff --name-only | grep -E "\.(yaml|yml|json)$" | head -5)
if [[ ! -z "$AWS_CHANGES" ]]; then
    echo "🔍 AWS configuration changes detected - reviewing for security vulnerabilities:"
    echo "$AWS_CHANGES"
    # Check for common security issues
    for file in $AWS_CHANGES; do
        if [[ -f "$file" ]]; then
            echo "🔍 Reviewing $file for security issues..."
            # Check for exposed credentials
            if grep -qi "password\|secret\|key\|token" "$file"; then
                echo "⚠️  WARNING: Potential exposed credentials in $file"
            fi
            # Check for overly permissive IAM policies
            if grep -qi "\"Effect\": \"Allow\"" "$file" && grep -qi "\"Action\": \"\*\"" "$file"; then
                echo "⚠️  WARNING: Overly permissive IAM policy detected in $file"
            fi
            # Check for public S3 buckets
            if grep -qi "\"Effect\": \"Allow\"" "$file" && grep -qi "s3:\|\"Principal\": \"\*\"" "$file"; then
                echo "⚠️  WARNING: Potential public S3 access in $file"
            fi
        fi
    done
fi
```

### Development Session Enforcement

### Start of Development Session
```bash
# Run this before any implementation
echo "🔍 Checking implementation norms compliance..."
echo "Current markdown files:"
find . -name "*.md" | grep -v node_modules
echo "Current config files:"  
find . -name "*.yaml" -o -name "*.yml" -o -name ".env*" | grep -v node_modules
echo "✅ Ready for development - stick to existing files!"
```

### During Vibe Coding
**Automatic Prompts:**
- When creating new file: "❌ Check if this can be added to existing file instead"
- When editing documentation: "✅ Good - updating existing doc/aws-deployment-plan.md"
- When adding config: "✅ Good - modifying existing configuration file"
- When temporary files detected: "⚠️ Review Windsurf-created files for cleanup"
- When AWS changes detected: "🔒 Running security vulnerability assessment..."

### End of Development Session
```bash
# Compliance verification
echo "📊 Session Compliance Check:"
echo "✅ No new markdown files created"
echo "✅ No new config files created" 
echo "✅ Documentation updated in aws-deployment-plan.md"
echo "🔍 Checking for temporary files to cleanup..."
find . -name "*.tmp" -o -name "*~" -o -name "*.bak" -o -name "*.orig" | grep -v node_modules || echo "✅ No temporary files found"
echo "🔒 Final security vulnerability assessment..."
# Check for any AWS changes in the session
if git diff --name-only HEAD~1 | grep -E "\.(yaml|yml|json)$" >/dev/null 2>&1; then
    echo "🔍 AWS configuration changes detected - security review completed"
else
    echo "✅ No AWS configuration changes detected"
fi
echo "🔄 Final AWS config sync check..."
# Verify all AWS config files are present and consistent
AWS_CONFIGS=("infra/aws/template.yaml" "infra/aws/template-minimal.yaml" "infra/aws/template-lambda-only.yaml")
for config in "${AWS_CONFIGS[@]}"; do
    if [[ -f "$config" ]]; then
        echo "✅ $config present"
    else
        echo "⚠️  $config missing"
    fi
done
```

## Memory Storage
These norms are stored in memory and should be referenced for all implementations. The system should automatically check compliance before proceeding with any implementation.
