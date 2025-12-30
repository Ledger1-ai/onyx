#!/usr/bin/env python3
"""
Account Manager for Twitter Super Agent
View and manage dynamically discovered accounts
"""

import sqlite3
import argparse
from datetime import datetime, timedelta
import json

def view_discovered_accounts(min_score=0.0, limit=20):
    """View discovered accounts with their scores"""
    try:
        conn = sqlite3.connect('super_agent.db')
        cursor = conn.execute("""
            SELECT username, relevance_score, discovery_reason, bio, 
                   follower_count, last_evaluated, timestamp 
            FROM discovered_accounts 
            WHERE relevance_score >= ? 
            ORDER BY relevance_score DESC, follower_count DESC 
            LIMIT ?
        """, (min_score, limit))
        
        accounts = cursor.fetchall()
        conn.close()
        
        if not accounts:
            print("📭 No discovered accounts found")
            return
        
        print(f"🔍 Discovered Accounts (min score: {min_score})")
        print("━" * 80)
        
        for account in accounts:
            username, score, reason, bio, followers, last_eval, timestamp = account
            
            print(f"🎯 @{username}")
            print(f"   📊 Relevance Score: {score:.2f}")
            print(f"   👥 Followers: {followers:,}" if followers else "   👥 Followers: Unknown")
            print(f"   🔍 Discovery: {reason}")
            print(f"   📝 Bio: {bio[:100]}..." if bio and len(bio) > 100 else f"   📝 Bio: {bio}")
            print(f"   🕒 Discovered: {timestamp}")
            print(f"   🔄 Last Evaluated: {last_eval}")
            print()
            
    except Exception as e:
        print(f"❌ Error viewing accounts: {e}")

def export_accounts(filename="discovered_accounts.json", min_score=0.7):
    """Export discovered accounts to JSON file"""
    try:
        conn = sqlite3.connect('super_agent.db')
        cursor = conn.execute("""
            SELECT username, relevance_score, discovery_reason, bio, 
                   follower_count, last_evaluated, timestamp 
            FROM discovered_accounts 
            WHERE relevance_score >= ? 
            ORDER BY relevance_score DESC
        """, (min_score,))
        
        accounts = []
        for row in cursor.fetchall():
            username, score, reason, bio, followers, last_eval, timestamp = row
            accounts.append({
                "username": username,
                "relevance_score": score,
                "discovery_reason": reason,
                "bio": bio,
                "follower_count": followers,
                "last_evaluated": last_eval,
                "discovered_at": timestamp
            })
        
        conn.close()
        
        with open(filename, 'w') as f:
            json.dump(accounts, f, indent=2)
            
        print(f"✅ Exported {len(accounts)} accounts to {filename}")
        
    except Exception as e:
        print(f"❌ Error exporting accounts: {e}")

def get_account_stats():
    """Get statistics about discovered accounts"""
    try:
        conn = sqlite3.connect('super_agent.db')
        
        # Total accounts
        total = conn.execute("SELECT COUNT(*) FROM discovered_accounts").fetchone()[0]
        
        # High relevance accounts (>= 0.7)
        high_relevance = conn.execute("SELECT COUNT(*) FROM discovered_accounts WHERE relevance_score >= 0.7").fetchone()[0]
        
        # Medium relevance accounts (0.5-0.7)
        medium_relevance = conn.execute("SELECT COUNT(*) FROM discovered_accounts WHERE relevance_score >= 0.5 AND relevance_score < 0.7").fetchone()[0]
        
        # Recently evaluated (last week)
        one_week_ago = datetime.now() - timedelta(days=7)
        recent_eval = conn.execute("SELECT COUNT(*) FROM discovered_accounts WHERE last_evaluated > ?", (one_week_ago,)).fetchone()[0]
        
        # Average score
        avg_score = conn.execute("SELECT AVG(relevance_score) FROM discovered_accounts").fetchone()[0]
        
        # Top scoring account
        top_account = conn.execute("SELECT username, relevance_score FROM discovered_accounts ORDER BY relevance_score DESC LIMIT 1").fetchone()
        
        conn.close()
        
        print("📊 Account Discovery Statistics")
        print("━" * 40)
        print(f"📈 Total Discovered: {total}")
        print(f"🎯 High Relevance (≥0.7): {high_relevance}")
        print(f"📊 Medium Relevance (0.5-0.7): {medium_relevance}")
        print(f"🔄 Recently Evaluated: {recent_eval}")
        print(f"⭐ Average Score: {avg_score:.3f}" if avg_score else "⭐ Average Score: N/A")
        
        if top_account:
            print(f"🏆 Top Account: @{top_account[0]} ({top_account[1]:.3f})")
        
    except Exception as e:
        print(f"❌ Error getting stats: {e}")

def update_account_score(username, new_score):
    """Manually update an account's relevance score"""
    try:
        conn = sqlite3.connect('super_agent.db')
        
        # Check if account exists
        cursor = conn.execute("SELECT username FROM discovered_accounts WHERE username = ?", (username,))
        if not cursor.fetchone():
            print(f"❌ Account @{username} not found in database")
            conn.close()
            return
        
        # Update score
        conn.execute("UPDATE discovered_accounts SET relevance_score = ?, last_evaluated = ? WHERE username = ?",
                    (new_score, datetime.now(), username))
        conn.commit()
        conn.close()
        
        print(f"✅ Updated @{username} relevance score to {new_score}")
        
    except Exception as e:
        print(f"❌ Error updating account: {e}")

def remove_account(username):
    """Remove an account from discovered accounts"""
    try:
        conn = sqlite3.connect('super_agent.db')
        
        # Check if account exists
        cursor = conn.execute("SELECT username FROM discovered_accounts WHERE username = ?", (username,))
        if not cursor.fetchone():
            print(f"❌ Account @{username} not found in database")
            conn.close()
            return
        
        # Remove account
        conn.execute("DELETE FROM discovered_accounts WHERE username = ?", (username,))
        conn.commit()
        conn.close()
        
        print(f"✅ Removed @{username} from discovered accounts")
        
    except Exception as e:
        print(f"❌ Error removing account: {e}")

def main():
    parser = argparse.ArgumentParser(description='Manage discovered Twitter accounts')
    parser.add_argument('--view', action='store_true', help='View discovered accounts')
    parser.add_argument('--stats', action='store_true', help='Show account statistics')
    parser.add_argument('--export', type=str, help='Export accounts to JSON file')
    parser.add_argument('--min-score', type=float, default=0.0, help='Minimum relevance score to display')
    parser.add_argument('--limit', type=int, default=20, help='Maximum number of accounts to display')
    parser.add_argument('--update-score', nargs=2, metavar=('USERNAME', 'SCORE'), help='Update account score')
    parser.add_argument('--remove', type=str, help='Remove account from database')
    
    args = parser.parse_args()
    
    if args.view:
        view_discovered_accounts(args.min_score, args.limit)
    elif args.stats:
        get_account_stats()
    elif args.export:
        export_accounts(args.export, args.min_score)
    elif args.update_score:
        username, score = args.update_score
        try:
            score = float(score)
            if 0.0 <= score <= 1.0:
                update_account_score(username, score)
            else:
                print("❌ Score must be between 0.0 and 1.0")
        except ValueError:
            print("❌ Invalid score format")
    elif args.remove:
        remove_account(args.remove)
    else:
        # Interactive mode
        print("🔧 Account Manager - Interactive Mode")
        print("Available commands:")
        print("  1. View discovered accounts")
        print("  2. Show statistics")
        print("  3. Export accounts")
        print("  4. Update account score")
        print("  5. Remove account")
        print("  6. Exit")
        
        while True:
            try:
                choice = input("\nEnter your choice (1-6): ").strip()
                
                if choice == "1":
                    min_score = float(input("Minimum relevance score (0.0-1.0): ") or "0.0")
                    limit = int(input("Maximum accounts to show (default 20): ") or "20")
                    view_discovered_accounts(min_score, limit)
                    
                elif choice == "2":
                    get_account_stats()
                    
                elif choice == "3":
                    filename = input("Export filename (default: discovered_accounts.json): ") or "discovered_accounts.json"
                    min_score = float(input("Minimum relevance score (default 0.7): ") or "0.7")
                    export_accounts(filename, min_score)
                    
                elif choice == "4":
                    username = input("Username (without @): ").strip()
                    score = float(input("New relevance score (0.0-1.0): "))
                    if 0.0 <= score <= 1.0:
                        update_account_score(username, score)
                    else:
                        print("❌ Score must be between 0.0 and 1.0")
                        
                elif choice == "5":
                    username = input("Username to remove (without @): ").strip()
                    confirm = input(f"Are you sure you want to remove @{username}? (y/N): ")
                    if confirm.lower() == 'y':
                        remove_account(username)
                    else:
                        print("Operation cancelled")
                        
                elif choice == "6":
                    print("👋 Goodbye!")
                    break
                    
                else:
                    print("❌ Invalid choice. Please enter 1-6.")
                    
            except (ValueError, EOFError, KeyboardInterrupt):
                print("\n👋 Goodbye!")
                break

if __name__ == "__main__":
    main() 