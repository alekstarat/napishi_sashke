from handlers.base import PacketContext, PacketHandler
from protocol.models import PublicKeyResponse, GetHistoryRequest, GetHistoryPayload


class PublicKeyHandler(PacketHandler[PublicKeyResponse]):
    packet_type = PublicKeyResponse

    async def handle(
            self,
            ctx: PacketContext,
            packet: PublicKeyResponse,
    ) -> None:
        ctx.client.peer_public_key = (
            ctx.client.crypto.import_public_key(
                packet.payload.public_key
            )
        )

        ctx.ui.system(
            f"Public key received for {packet.payload.username}"
        )

        await ctx.client.send(
            GetHistoryRequest(
                payload=GetHistoryPayload(
                    username=packet.payload.username,
                )
            )
        )