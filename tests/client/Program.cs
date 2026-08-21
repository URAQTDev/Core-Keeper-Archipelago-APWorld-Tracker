using System;
using System.Linq;
using CoreKeeperArchipelago.Mainline;
using CoreKeeperArchipelago.Mainline.State;

static void Assert(bool condition, string message)
{
    if (!condition)
    {
        throw new InvalidOperationException(message);
    }
}

var checks = new PendingLocationChecks();
Assert(checks.Add(3), "first location insertion must succeed");
Assert(!checks.Add(3), "duplicate locations must be idempotent");
checks.Add(1);
Assert(checks.Snapshot().SequenceEqual(new long[] { 1, 3 }), "location snapshots must be deterministic");
checks.Confirm(new long[] { 3 });
Assert(checks.Snapshot().SequenceEqual(new long[] { 1 }), "confirmed locations must leave the queue");

var cursor = new ReceivedItemCursor();
cursor.Restore(1, new[] { "old" });
var reservations = cursor.ReserveUndelivered(new[] { "old", "new-a", "new-b" }, item => item);
Assert(reservations.Select(item => item.Item).SequenceEqual(new[] { "new-a", "new-b" }),
    "cursor must skip already delivered items");
Assert(cursor.ReserveUndelivered(new[] { "old", "new-a", "new-b" }, item => item).Count == 0,
    "reserved items must not be enqueued twice before delivery");
foreach (var reservation in reservations) cursor.Commit(reservation.Index, reservation.Signature);
Assert(cursor.NextIndex == 3, "commits must advance the persistent cursor");
Assert(cursor.ReserveUndelivered(new[] { "old" }, item => item).Count == 0,
    "a transient shorter SDK list must never rewind a persisted room cursor");

var rolledBackServer = new ReceivedItemCursor();
rolledBackServer.Restore(3, new[] { "old-a", "old-b", "old-c" });
var replacement = rolledBackServer.ReserveUndelivered(new[] { "old-a", "new-b" }, item => item);
Assert(replacement.Count == 1 && replacement[0].Index == 1 && replacement[0].Item == "new-b",
    "a reused server index with a different item must be delivered after server rollback");
rolledBackServer.Commit(replacement[0].Index, replacement[0].Signature);
Assert(rolledBackServer.NextIndex == 3 && rolledBackServer.SignatureSnapshot()[1] == "new-b",
    "a replacement delivery must update identity without rewinding the high-water cursor");

var legacyCursor = new ReceivedItemCursor();
legacyCursor.Restore(2);
var legacyReservations = legacyCursor.ReserveUndelivered(new[] { "legacy-a", "legacy-b", "new-c" }, item => item);
Assert(legacyReservations.Count == 1 && legacyReservations[0].Item == "new-c",
    "legacy cursor-only state must learn existing identities without replaying old rewards");
Assert(legacyCursor.SignatureSnapshot().SequenceEqual(new[] { "legacy-a", "legacy-b" }),
    "legacy migration must persist an identity prefix for future rollback detection");

var replacementRoomCursor = new ReceivedItemCursor();
replacementRoomCursor.Restore(0);
Assert(replacementRoomCursor.ReserveUndelivered(new[] { "replacement-room-item" }, item => item)
        .Select(item => item.Item).SequenceEqual(new[] { "replacement-room-item" }),
    "a new room's independently restored cursor must deliver its first item");

var duplicates = new ReceivedItemCursor();
string[] duplicateItems = { "same", "same", "same" };
var duplicateReservations = duplicates.ReserveUndelivered(duplicateItems, item => item);
Assert(duplicateReservations.Select(item => item.Item).SequenceEqual(duplicateItems),
    "received item cursor must preserve arbitrary duplicate items by index");
foreach (var reservation in duplicateReservations) duplicates.Commit(reservation.Index, reservation.Signature);
Assert(duplicates.NextIndex == 3, "duplicate deliveries must each advance the cursor once");

var offlineChecks = new PendingLocationChecks();
offlineChecks.Restore(new long[] { 9, 7, 9 });
Assert(offlineChecks.Snapshot().SequenceEqual(new long[] { 7, 9 }),
    "offline-restored checks must remain unique and deterministic");

var backoff = new ReconnectBackoff();
int[] delays = Enumerable.Range(0, 8).Select(_ => (int)backoff.NextDelay().TotalSeconds).ToArray();
Assert(delays.SequenceEqual(new[] { 1, 2, 4, 8, 16, 30, 30, 30 }), "reconnect delay must be bounded exponential backoff");
backoff.Reset();
Assert(backoff.NextDelay() == TimeSpan.FromSeconds(1), "successful connection must reset backoff");

Assert(ConnectionSettings.NormalizeServer("wss://archipelago.gg:64223") == "wss://archipelago.gg:64223",
    "explicit secure web-host transport must be preserved");
Assert(ConnectionSettings.NormalizeServer(" wss://custom.example:443 ") == "wss://custom.example:443",
    "explicit custom secure transports must be preserved");
Assert(ConnectionSettings.IsValidServer("wss://archipelago.gg:64223"), "secure web-host room address must validate");
Assert(!ConnectionSettings.IsValidServer("not a server"), "malformed address must be rejected");

var threeBossGoal = GoalLocationPolicy.Parse(
    new System.Collections.Generic.Dictionary<string, object>
    {
        ["slot_data_version"] = 1,
        ["goal"] = 3,
        ["goal_location_ids"] = new object[] { 8406404L, 8406402L, 8406403L, 8406402L }
    }, 1, 8406402L);
Assert(threeBossGoal.SequenceEqual(new long[] { 8406402L, 8406403L, 8406404L }),
    "multi-location goals must be unique and deterministic");
var confirmedBosses = new System.Collections.Generic.HashSet<long> { 8406402L, 8406403L };
Assert(!GoalLocationPolicy.AreAllConfirmed(threeBossGoal, confirmedBosses.Contains),
    "Lower Wall must not complete after only two pre-wall bosses");
confirmedBosses.Add(8406404L);
Assert(GoalLocationPolicy.AreAllConfirmed(threeBossGoal, confirmedBosses.Contains),
    "Lower Wall must complete after all three pre-wall bosses");
bool malformedAllBossesRejected = false;
try
{
    GoalLocationPolicy.Parse(
        new System.Collections.Generic.Dictionary<string, object>
        {
            ["slot_data_version"] = 1,
            ["goal"] = 0,
            ["goal_location_ids"] = Enumerable.Range(0, 12).Select(value => (object)(8406400L + value)).ToArray()
        }, 1, 8406402L);
}
catch (InvalidOperationException)
{
    malformedAllBossesRejected = true;
}
Assert(malformedAllBossesRejected,
    "All Bosses rooms must be rejected unless all twenty boss requirements are supplied");

var licenses = new LicenseLedger();
Assert(licenses.GetWorkbenchLevel("room-a") == 0, "Basic Workbench must be the room default");
Assert(licenses.GrantWorkbench("room-a") == 1, "first progressive must unlock Copper Workbench");
Assert(licenses.GetWorkbenchLevel("room-b") == 0, "license progress must be isolated by room");
Assert(licenses.GrantAnvil("room-a") == 1, "first anvil progressive must unlock Copper Anvil");
Assert(licenses.GetAnvilLevel("room-b") == 0, "anvil progress must be isolated by room");
for (int index = 0; index < 10; index++)
{
    licenses.GrantWorkbench("room-a");
}
Assert(licenses.GetWorkbenchLevel("room-a") == 7, "extra progressives must do nothing after Solarite");
var restoredLicenses = new LicenseLedger();
restoredLicenses.Restore(licenses.Snapshot());
Assert(restoredLicenses.GetWorkbenchLevel("room-a") == 7,
    "license progress must survive reconnect and game restart persistence");
Assert(restoredLicenses.GetAnvilLevel("room-a") == 1,
    "anvil license progress must survive reconnect and game restart persistence");

var skillPoints = new SkillPointLedger();
Assert(skillPoints.Grant("room-a", 0, 5) == 5, "first skill reward must grant five points");
for (int index = 0; index < 10; index++) skillPoints.Grant("room-a", 0, 5);
Assert(skillPoints.Get("room-a", 0) == 25, "skill rewards must cap at twenty-five points");
Assert(skillPoints.Get("room-b", 0) == 0, "skill points must be isolated by room");
var restoredSkillPoints = new SkillPointLedger();
restoredSkillPoints.Restore(skillPoints.Snapshot());
Assert(restoredSkillPoints.Get("room-a", 0) == 25,
    "skill-point rewards must survive reconnect and game restart persistence");

var legendary = new LegendaryLedger();
Assert(legendary.Get("room-a") == 0, "legendary progress must start at the first reward");
for (int index = 0; index < 10; index++) legendary.Advance("room-a");
Assert(legendary.Get("room-a") == 6, "legendary progress must stop after all six rewards");
Assert(legendary.Get("room-b") == 0, "legendary progress must be isolated by room");
var restoredLegendary = new LegendaryLedger();
restoredLegendary.Restore(legendary.Snapshot());
Assert(restoredLegendary.Get("room-a") == 6,
    "legendary progress must survive reconnect and game restart persistence");

var provenance = new RewardProvenanceLedger();
provenance.Set("room-a", new RewardProvenanceSnapshot
{
    Pending = new System.Collections.Generic.Dictionary<int, int> { [1001] = 2 },
    Held = new System.Collections.Generic.Dictionary<int, int> { [1003] = 4 },
    Away = new System.Collections.Generic.Dictionary<int, int> { [1006] = 1 },
});
var restoredProvenance = new RewardProvenanceLedger();
restoredProvenance.Restore(provenance.Snapshot());
var roomAProvenance = restoredProvenance.Get("room-a");
Assert(roomAProvenance.Pending[1001] == 2 && roomAProvenance.Held[1003] == 4
       && roomAProvenance.Away[1006] == 1,
    "reward provenance must survive a complete game restart");
Assert(restoredProvenance.Get("room-b").Held.Count == 0,
    "reward provenance must remain isolated by AP room");

Console.WriteLine("Client state tests passed.");
