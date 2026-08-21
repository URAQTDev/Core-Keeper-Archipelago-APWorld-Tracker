using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Threading;
using Archipelago.MultiClient.Net.Helpers;
using Archipelago.MultiClient.Net.Models;
using CoreKeeperArchipelago.Mainline.State;

namespace CoreKeeperArchipelago.Mainline;

internal static class Program
{
    private const long CollectWood = 8406004;
    private const long DefeatGlurch = 8406402;
    private const long CopperKey = 8405001;

    private static int Main(string[] args)
    {
        if (args.Length != 2 || !ConnectionSettings.IsValidServer(args[0]))
        {
            Console.Error.WriteLine("usage: transport-test <ws-or-wss-server> <slot>");
            return 2;
        }

        var logs = new ConcurrentQueue<string>();
        var deliveries = new ConcurrentQueue<long>();
        var persisted = new Dictionary<string, int>(StringComparer.Ordinal);
        var persistedSignatures = new Dictionary<string, IReadOnlyList<string>>(StringComparer.Ordinal);
        var persistedChecks = new Dictionary<string, IReadOnlyCollection<long>>(StringComparer.Ordinal);
        var pending = new PendingLocationChecks();
        var cursor = new ReceivedItemCursor();
        var settings = new ConnectionSettings
        {
            Server = ConnectionSettings.NormalizeServer(args[0]),
            Slot = args[1],
            Uuid = "core-keeper-mainline-transport-test"
        };
        int deliveredBeforeReconnect;

        using (var connection = CreateConnection(
            pending, cursor, logs, deliveries, persisted, persistedSignatures, persistedChecks))
        {
            connection.Start(settings);
            WaitUntil(connection, logs, () => Contains(logs, "Saved. Connected."), "initial connection");
            connection.QueueLocationCheck(CollectWood);
            WaitUntil(connection, logs, () => deliveries.Count == 1, "Copper Key delivery");

            if (!deliveries.TryPeek(out long delivered) || delivered != CopperKey)
            {
                throw new InvalidOperationException("Collect Wood delivered unexpected item " + delivered + ".");
            }

            WaitUntil(connection, logs, () => pending.Snapshot().Length == 0, "location acknowledgement");
            connection.QueueLocationCheck(DefeatGlurch);
            WaitUntil(connection, logs, () => Contains(logs, "Goal complete."), "goal status update");
            Pump(connection, 1000);
            deliveredBeforeReconnect = deliveries.Count;
        }

        Thread.Sleep(250);
        var secondPending = new PendingLocationChecks();
        var secondCursor = new ReceivedItemCursor();
        using (var connection = CreateConnection(
            secondPending, secondCursor, logs, deliveries, persisted, persistedSignatures, persistedChecks))
        {
            connection.Start(settings);
            WaitUntil(connection, logs, () => Count(logs, "Saved. Connected.") >= 2, "reconnection");
            Pump(connection, 1500);
        }

        if (deliveries.Count != deliveredBeforeReconnect)
        {
            throw new InvalidOperationException(
                "Reconnect redelivered acknowledged items; before "
                + deliveredBeforeReconnect + ", after " + deliveries.Count + ".");
        }

        if (CompressedWebSocketClient.SuccessfulCompressionNegotiations < 2
            || CompressedWebSocketClient.CompressedFramesSent == 0
            || CompressedWebSocketClient.CompressedFramesReceived == 0)
        {
            throw new InvalidOperationException(
                "Compressed WebSocket transport was not exercised in both directions."
                + " negotiations=" + CompressedWebSocketClient.SuccessfulCompressionNegotiations
                + ", sent=" + CompressedWebSocketClient.CompressedFramesSent
                + ", received=" + CompressedWebSocketClient.CompressedFramesReceived + ".");
        }

        Console.WriteLine("PASS compressed real server transport, location acknowledgement, goal status, item delivery, cursor persistence, and reconnect deduplication");
        return 0;
    }

    private static ArchipelagoConnection CreateConnection(
        PendingLocationChecks pending,
        ReceivedItemCursor cursor,
        ConcurrentQueue<string> logs,
        ConcurrentQueue<long> deliveries,
        Dictionary<string, int> persisted,
        Dictionary<string, IReadOnlyList<string>> persistedSignatures,
        Dictionary<string, IReadOnlyCollection<long>> persistedChecks)
        => new ArchipelagoConnection(
            pending,
            cursor,
            item => Deliver(item, deliveries),
            room => persisted.TryGetValue(room, out int value) ? value : 0,
            (room, value) => persisted[room] = value,
            room => persistedSignatures.TryGetValue(room, out IReadOnlyList<string>? value)
                ? value
                : Array.Empty<string>(),
            (room, value) => persistedSignatures[room] = value.ToArray(),
            room => persistedChecks.TryGetValue(room, out IReadOnlyCollection<long>? value)
                ? value
                : Array.Empty<long>(),
            (room, value) => persistedChecks[room] = value.ToArray(),
            _ => { },
            (_, _) => { },
            message => { logs.Enqueue(message); Console.WriteLine(message); });

    private static bool Deliver(ItemInfo item, ConcurrentQueue<long> deliveries)
    {
        deliveries.Enqueue(item.ItemId);
        return true;
    }

    private static void WaitUntil(
        ArchipelagoConnection connection,
        ConcurrentQueue<string> logs,
        Func<bool> predicate,
        string operation)
    {
        var timer = Stopwatch.StartNew();
        while (timer.Elapsed < TimeSpan.FromSeconds(15))
        {
            connection.Update();
            if (predicate())
            {
                return;
            }
            Thread.Sleep(20);
        }

        throw new TimeoutException("Timed out waiting for " + operation + ". Logs: " + string.Join(" | ", logs));
    }

    private static void Pump(ArchipelagoConnection connection, int milliseconds)
    {
        var timer = Stopwatch.StartNew();
        while (timer.ElapsedMilliseconds < milliseconds)
        {
            connection.Update();
            Thread.Sleep(20);
        }
    }

    private static bool Contains(ConcurrentQueue<string> logs, string value)
        => Count(logs, value) != 0;

    private static int Count(ConcurrentQueue<string> logs, string value)
    {
        int count = 0;
        foreach (string entry in logs)
        {
            if (entry == value)
            {
                count++;
            }
        }
        return count;
    }
}
