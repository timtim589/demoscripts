#!/bin/bash

# Function to check if a file is writable by the current user
check_writable() {
    if [ -w "$1" ]; then
        echo -e "\033[92mSUCCESS: The file '$1' is writable by the current user and can be hijacked!\033[0m"
    else
        echo -e "\033[91mFAILURE: The file '$1' is not writable by the current user.\033[0m"
    fi
}

# Function to extract and check scripts from cron jobs
process_cron_line() {
    local line="$1"
    local script

    # Extract the command part of the cron job
    script=$(echo "$line" | sed -E 's/^[^ ]+ +[^ ]+ +[^ ]+ +[^ ]+ +[^ ]+ +[^ ]+ +//')
    
    if [ -n "$script" ]; then
        # Extract the first word of the command, which is usually the script or command being run
        script=$(echo "$script" | awk '{print $1}')
        check_writable "$script"
    fi
}

# Print all cron jobs for root from /etc/crontab
echo "Checking /etc/crontab for root cron jobs..."
grep -E '^.*root' /etc/crontab | while read -r line; do
    echo "Found cron job: $line"
    process_cron_line "$line"
done

# Print all cron jobs for root from /etc/cron.d/
echo "Checking /etc/cron.d/ for root cron jobs..."
for file in /etc/cron.d/*; do
    grep -E '^.*root' "$file" | while read -r line; do
        echo "Found cron job in $file: $line"
        process_cron_line "$line"
    done
done

# Print all cron jobs for root from root's crontab
echo "Checking root's crontab for cron jobs..."
sudo crontab -l -u root | grep -E '^.*' | while read -r line; do
    echo "Found cron job: $line"
    process_cron_line "$line"
done

